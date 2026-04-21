"""
Content Agent Core.
Takes a structured brief + Voice Document, generates platform-specific content variants,
runs each through the humanizer quality gate, returns passing outputs.
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
import anthropic
from .humanizer import check_and_rewrite, score_content
from .voice_builder import load_voice_document


# ─── Brief Model ──────────────────────────────────────────────────────────────

class ContentFormat(str, Enum):
    OPINION = "opinion"           # Original take on a topic
    REACTION = "reaction"         # Response to news or someone else's post
    EXPERIENCE = "experience"     # Lesson from a specific past campaign or build
    DATA = "data"                 # Specific observation or number shared raw
    NARRATIVE = "narrative"       # Hijacking a trending topic in the space


@dataclass
class ContentBrief:
    client_id: str
    topic: str                            # What the post is about
    angle: str                            # The specific take or argument
    format: ContentFormat = ContentFormat.OPINION
    credential: str = ""                  # Specific experience to reference (optional)
    data_point: str = ""                  # Specific number or outcome to include (optional)
    source_url: str = ""                  # URL to react to (for reaction posts)
    source_text: str = ""                 # Pasted context (for reaction or narrative posts)
    platform_priority: str = "linkedin"   # Primary platform: linkedin / x / both
    company_voice: bool = False           # True = company "we" voice, False = personal "I" voice
    voice_version: int = None             # Specific voice version, None = latest
    voices_path: str = "voices"


@dataclass
class ContentOutput:
    linkedin_long: str
    linkedin_short: str
    x_thread: list[str]
    x_single: str
    community_message: str
    scores: dict
    passed_gate: bool
    patterns_found: list[dict]


# ─── System Prompt Builder ────────────────────────────────────────────────────

def build_system_prompt(voice_document: str, company_voice: bool = False) -> str:
    voice_mode = "company" if company_voice else "personal"
    pov_instruction = (
        "Write in the company's voice — use 'we', 'our', 'the team'. "
        "Perspective is the company sharing what it has learned and built, not a founder's personal narrative. "
        "Reference the company name and products naturally."
        if company_voice else
        "Write in first person — 'I', 'my', 'we' where team is referenced. "
        "Perspective is the founder/operator sharing personal experience and hard-won insight."
    )

    return f"""You are a professional content writer generating social media posts for a specific {voice_mode}.

{voice_document}

---

## VOICE MODE: {voice_mode.upper()}

{pov_instruction}

---

## WHAT MAKES CONTENT WORTH READING

Good content does one of three things: it surprises the reader, it makes them feel understood, or it gives them something specific they didn't have before. Boring content does none of these — it explains a topic people already know exists.

Before writing, ask:
- What is the most counterintuitive or surprising thing about this topic?
- What specific detail would only someone with real firsthand experience know?
- What is the stake — what actually goes wrong for people who get this wrong?
- Is there a moment, a number, or a contrast that makes this concrete?

**The hook must earn attention.** The first sentence is not scene-setting. It is the sharpest, most specific, most surprising version of the point. If the first sentence could appear in a generic blog post about this topic, rewrite it.

**Every paragraph must add something new.** Not restate. Not expand. Add. If a paragraph could be cut and the reader would lose nothing, cut it.

**Stakes make content shareable.** "Here is how something works" is forgettable. "Here is what it costs you when you get this wrong, and here is why smart people keep getting it wrong" is a post people screenshot.

**Be willing to take a position that someone could argue with.** Safe content that hedges everything performs badly. Write a clear claim. Back it with specifics. Let it stand.

A post passes the Turing test if:
- A reader in this industry stops scrolling because the first sentence says something they haven't heard phrased that way
- The specific details could only come from someone who lived this
- The position is clear enough that someone could disagree with it
- The ending adds something — it doesn't summarise what already came before

---

## OUTPUT REQUIREMENTS

Return ONLY valid JSON. No markdown fences, no preamble. Exact structure:

{{
  "linkedin_long": "600-900 words. No headers. No bullets. One continuous argument. HOOK: first 1-2 sentences are the sharpest, most surprising version of the point — no warm-up, no context-setting. BUILD: each paragraph adds something new, not a restatement. STAKES: include what actually goes wrong when people get this wrong. SPECIFICS: at least one detail that proves firsthand experience. LANDING: a sharp final observation — not a summary, not a CTA, not inspiration.",
  "linkedin_short": "150-250 words. One counterintuitive observation turned into a full point. First sentence stops the scroll. Middle earns the point with a specific. Last sentence is a landing, not a prompt to engage.",
  "x_thread": ["tweet 1: the most surprising or counterintuitive claim — specific enough to be arguable, works as a standalone", "tweet 2: the mechanism — the specific reason this is true that most people don't know", "tweet 3: a concrete number, timeline, or example that makes it real", "tweet 4: the implication — what this means for someone in the reader's position", "tweet 5: the thing that makes it harder than it looks — a specific friction point", "tweet 6: what the wrong approach looks like — specific enough to be recognisable", "tweet 7: what the right approach actually requires — practical, not abstract", "tweet 8: a landing observation that reframes the whole thread — not a summary, not a call to action"],
  "x_single": "Under 240 characters. One specific, arguable claim. The kind of tweet someone screenshots and sends to a colleague. No hashtags.",
  "community_message": "100-150 words. Conversational. Drops one specific insight and invites a reaction. Sounds like a message someone would actually type in a group chat."
}}

---

## ABSOLUTE RULES — NEVER BREAK THESE

- No em dashes anywhere. Not one. Use commas, colons, or restructure the sentence.
- No ellipsis (...) anywhere. Complete the thought or cut it.
- No rhetorical setup constructions: never "X is not the problem. Y is the problem." State Y directly.
- No serial negation: never stack "not X. not Y. it is Z." Lead with Z.
- No banned words or phrases from the voice document
- Never fabricate numbers, outcomes, or quotes not given in the brief
- No hollow endings: no "only time will tell", no "the future is bright", no "exciting times ahead"
- Tweets must each contain a distinct idea — not variations of the same sentence restated differently
- Professional and direct — not casual, not cold, not corporate"""


# ─── Generation ───────────────────────────────────────────────────────────────

def build_user_message(brief: ContentBrief) -> str:
    msg = f"Generate content from this brief:\n\n"
    msg += f"**Topic:** {brief.topic}\n"
    msg += f"**Angle:** {brief.angle}\n"
    msg += f"**Format:** {brief.format.value}\n"

    if brief.credential:
        msg += f"**Specific credential to reference:** {brief.credential}\n"
    if brief.data_point:
        msg += f"**Specific data point to include:** {brief.data_point}\n"
    if brief.source_url:
        msg += f"**Source URL:** {brief.source_url}\n"
    if brief.source_text:
        msg += f"**Source content to react to:**\n{brief.source_text[:2000]}\n"

    msg += f"\n**Platform priority:** {brief.platform_priority}"
    return msg


def generate_content(
    brief: ContentBrief,
    client: anthropic.Anthropic,
    auto_rewrite: bool = True
) -> ContentOutput:
    """
    Main generation function. Loads voice doc, generates content, runs quality gate.
    """
    # Load voice document
    voice_doc = load_voice_document(
        brief.client_id,
        version=brief.voice_version,
        base_path=brief.voices_path
    )

    system = build_system_prompt(voice_doc, company_voice=brief.company_voice)
    user_msg = build_user_message(brief)

    # Generate
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": user_msg}]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r'```json|```', '', raw).strip()
    generated = json.loads(raw)

    # Quality gate each variant
    variants = {
        "linkedin_long": generated.get("linkedin_long", ""),
        "linkedin_short": generated.get("linkedin_short", ""),
        "x_single": generated.get("x_single", ""),
        "community_message": generated.get("community_message", "")
    }

    gate_results = {}
    all_patterns = []
    all_passed = True

    for key, text in variants.items():
        if text:
            result = check_and_rewrite(text, voice_doc, client, auto_rewrite)
            gate_results[key] = result
            all_patterns.extend(result.get("patterns_found", []))
            if not result.get("passes", True):
                all_passed = False

    # Gate X thread as a whole
    thread_text = " ".join(generated.get("x_thread", []))
    thread_result = check_and_rewrite(thread_text, voice_doc, client, auto_rewrite=False)
    gate_results["x_thread"] = thread_result

    # Build output
    scores = {
        key: {
            "before": r.get("score_before", 1),
            "after": r.get("score_after", 1)
        }
        for key, r in gate_results.items()
    }

    return ContentOutput(
        linkedin_long=gate_results["linkedin_long"].get("rewritten", variants["linkedin_long"]),
        linkedin_short=gate_results["linkedin_short"].get("rewritten", variants["linkedin_short"]),
        x_thread=generated.get("x_thread", []),
        x_single=gate_results["x_single"].get("rewritten", variants["x_single"]),
        community_message=gate_results["community_message"].get("rewritten", variants["community_message"]),
        scores=scores,
        passed_gate=all_passed,
        patterns_found=all_patterns
    )


# ─── Narrative Fast-Path ──────────────────────────────────────────────────────

def generate_reaction(
    client_id: str,
    narrative_text: str,
    narrative_source: str,
    client: anthropic.Anthropic,
    voices_path: str = "voices"
) -> dict:
    """
    Fast-path generation for narrative hijacking.
    Takes a trending topic or breaking news item, generates a reaction post quickly.
    Optimised for speed: returns LinkedIn short + X single only.
    """
    voice_doc = load_voice_document(client_id, base_path=voices_path)

    system = f"""You are generating a fast reaction post for a breaking narrative.

{voice_doc}

Generate a reaction that:
- Responds to the specific thing that happened, not a generic take on the topic
- Uses the brand's voice and draws on their specific experience
- Takes a clear position — don't sit on the fence
- Is timely without being reckless

Return ONLY valid JSON:
{{
  "linkedin_short": "150-250 word LinkedIn reaction post",
  "x_single": "single tweet under 240 chars taking a clear position"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Source: {narrative_source}\n\nContent:\n{narrative_text[:1500]}"
        }]
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r'```json|```', '', raw).strip()
    result = json.loads(raw)

    # Quick score check (no auto-rewrite on fast path)
    for key in ["linkedin_short", "x_single"]:
        if result.get(key):
            score = score_content(result[key])
            result[f"{key}_score"] = score.score

    return result
