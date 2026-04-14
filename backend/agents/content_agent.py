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

def build_system_prompt(voice_document: str) -> str:
    return f"""You are a content writer generating social media content for a specific person or brand.

{voice_document}

---

## OUTPUT REQUIREMENTS

Return ONLY valid JSON. No markdown fences, no preamble. Exact structure:

{{
  "linkedin_long": "Full long-form LinkedIn post (600-900 words). No headers. No bullet lists. One continuous human argument. Hook in first 1-3 sentences. Develops with depth. Ends with specific takeaway or open observation, never a CTA.",
  "linkedin_short": "Short LinkedIn post (150-250 words). One sharp observation. 2-3 paragraphs. First line must work as a standalone sentence. No CTA at end.",
  "x_thread": ["tweet 1 (hook, works standalone)", "tweet 2", "tweet 3", "tweet 4", "tweet 5", "tweet 6", "tweet 7", "tweet 8 (landing, not a summary)"],
  "x_single": "Single tweet under 240 characters. No hashtags. One observation.",
  "community_message": "Discord/Telegram message variant (100-150 words). Slightly more conversational. Same substance."
}}

## CRITICAL RULES

- Never use em dashes anywhere
- Never use banned words from the voice document
- Never use banned phrases from the voice document
- Draw on specific credentials and real experience where relevant
- Never fabricate numbers or outcomes not provided in the brief
- LinkedIn long-form: reads as written by a human who thought carefully about one thing
- X thread: each tweet one idea, numbers and specifics in at least 3 middle tweets
- If source text is provided, react to it specifically, not generically"""


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

    system = build_system_prompt(voice_doc)
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
