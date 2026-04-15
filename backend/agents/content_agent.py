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

## QUALITY BAR — READ THIS BEFORE WRITING

Before writing a single word, define what a good post looks like for this brief:
- What is the ONE thing this post needs to make the reader understand or feel?
- What specific fact, number, or observation makes this credible?
- What would a senior operator in this industry find worth sharing?

A post passes the Turing test if:
- A human expert in this field would nod reading it
- You could not remove the author's name and paste it on another account
- It contains at least one specific detail that could only come from direct experience
- It does not try to sound smart — it just is

A post fails if:
- It uses rhetorical setup structures ("The problem is not X. The real problem is Y.")
- It lists observations without building to a single clear conclusion
- It reads like a summary of a topic rather than a take on it
- Any sentence could be deleted without losing meaning

---

## OUTPUT REQUIREMENTS

Return ONLY valid JSON. No markdown fences, no preamble. Exact structure:

{{
  "linkedin_long": "Full long-form post (600-900 words). No headers. No bullet lists. One continuous argument that builds. Hook in first 1-2 sentences — specific and direct, no scene-setting. Each paragraph earns its place. Ends with a specific observation, not a CTA or summary.",
  "linkedin_short": "Short post (150-250 words). One sharp observation developed into a clear point. 2-3 paragraphs. First sentence works standalone. Last sentence is a conclusion, not a CTA.",
  "x_thread": ["tweet 1: hook — a specific claim or counterintuitive fact, works standalone", "tweet 2: the mechanism — why is this true?", "tweet 3: specific data point or real example", "tweet 4: the implication most people miss", "tweet 5: another concrete detail", "tweet 6: the common mistake", "tweet 7: what the right approach actually is", "tweet 8: landing — a specific conclusion, not a summary or inspiration quote"],
  "x_single": "Single tweet under 240 characters. One specific claim. No hashtags. No ellipsis.",
  "community_message": "Discord/Telegram message (100-150 words). More direct, less polished. Same substance, conversational register."
}}

---

## ABSOLUTE RULES — NEVER BREAK THESE

- No em dashes anywhere. Not one. Use commas, colons, or restructure.
- No ellipsis (...) anywhere. Complete the thought or cut it.
- No rhetorical setup: never write "X is not the problem. Y is the problem." State Y directly.
- No serial negation: never stack "not X. not Y. it is Z." Lead with Z.
- No banned words or phrases from the voice document
- Never fabricate numbers, outcomes, or quotes not given in the brief
- No hollow endings: no "only time will tell", no "the future is bright", no "exciting times ahead"
- No sycophantic openers in any format
- Tweets must each contain a distinct specific idea — not variations of the same sentence
- Professional tone throughout — confident, not casual; direct, not cold"""


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
