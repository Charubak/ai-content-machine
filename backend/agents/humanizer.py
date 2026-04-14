"""
Humanizer: 25-pattern AI writing quality gate.
Based on Wikipedia's "Signs of AI writing" guide and blader/humanizer.
Scores content and returns flagged patterns with rewrites.
"""

import re
import anthropic
from dataclasses import dataclass


# ─── Pattern Definitions ─────────────────────────────────────────────────────

BANNED_WORDS = [
    "delve", "tapestry", "vibrant", "pivotal", "landscape",
    "underscore", "testament", "interplay", "foster", "cultivate",
    "showcase", "stakeholders", "synergy", "robust", "seamless",
    "leverage", "cutting-edge", "game-changing", "thought leader",
    "innovative", "groundbreaking", "comprehensive", "multifaceted",
    "nuanced", "paradigm", "revolutionary", "transformative",
    "empower", "holistic", "dynamic", "actionable", "streamline",
    "garnered", "harnessing", "spearheading", "bolstering",
    "endeavor", "realm", "commendable", "pivotal",
]

BANNED_PHRASES = [
    "in today's rapidly evolving",
    "it's worth noting that",
    "it is worth noting",
    "at the end of the day",
    "this is a reminder that",
    "in conclusion",
    "to summarize",
    "as we have seen",
    "in today's world",
    "in the ever-evolving",
    "it goes without saying",
    "needless to say",
    "as previously mentioned",
    "without further ado",
    "first and foremost",
    "last but not least",
    "in today's fast-paced",
    "the world of",
    "a testament to",
    "stands as a",
    "serves as a",
    "more than ever before",
]

HOLLOW_AFFIRMATIVES = [
    r"^certainly[!,.]",
    r"^absolutely[!,.]",
    r"^great question",
    r"^of course[!,.]",
    r"^i completely understand",
    r"^that's a fascinating",
    r"^i hope this helps",
    r"^i'm glad you asked",
]

EM_DASH_PATTERN = r"—"
NEGATIVE_PARALLELISM = r"not only .{5,60} but (also )?[\w]"
HYPHENATED_PAIRS = r"\b(ever-evolving|thought-provoking|game-changing|fast-paced|wide-ranging|far-reaching|cutting-edge|well-established|long-standing|high-quality|in-depth|up-to-date|state-of-the-art)\b"


@dataclass
class PatternMatch:
    pattern_name: str
    example: str
    severity: str  # "high", "medium", "low"
    why: str


@dataclass
class HumanizerResult:
    score: int  # 1-10, 10 = pure slop
    patterns_found: list[PatternMatch]
    passes: bool  # True if score <= 4
    summary: str


# ─── Scoring Logic ────────────────────────────────────────────────────────────

def check_banned_words(text: str) -> list[PatternMatch]:
    matches = []
    text_lower = text.lower()
    for word in BANNED_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            matches.append(PatternMatch(
                pattern_name="AI Vocabulary Word",
                example=word,
                severity="high",
                why=f'"{word}" appears far more frequently in AI-generated text post-2023. Swap for a specific, direct alternative.'
            ))
    return matches


def check_banned_phrases(text: str) -> list[PatternMatch]:
    matches = []
    text_lower = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in text_lower:
            matches.append(PatternMatch(
                pattern_name="Filler Transition Phrase",
                example=phrase,
                severity="high",
                why="This phrase adds zero information and signals AI generation to any trained reader."
            ))
    return matches


def check_hollow_affirmatives(text: str) -> list[PatternMatch]:
    matches = []
    text_lower = text.lower()
    for pattern in HOLLOW_AFFIRMATIVES:
        if re.search(pattern, text_lower):
            matches.append(PatternMatch(
                pattern_name="Hollow Affirmative Opener",
                example=re.search(pattern, text_lower).group(),
                severity="high",
                why="Opening with affirmatives like 'Certainly!' is an immediate AI tell. Delete and start with substance."
            ))
    return matches


def check_em_dashes(text: str) -> list[PatternMatch]:
    count = len(re.findall(EM_DASH_PATTERN, text))
    if count >= 2:
        return [PatternMatch(
            pattern_name="Em Dash Overuse",
            example=f"{count} em dashes found",
            severity="medium",
            why="Multiple em dashes in a single piece is a strong AI signal. Use commas, colons, or restructure."
        )]
    return []


def check_negative_parallelisms(text: str) -> list[PatternMatch]:
    matches = re.findall(NEGATIVE_PARALLELISM, text, re.IGNORECASE)
    if matches:
        return [PatternMatch(
            pattern_name="Negative Parallelism",
            example=matches[0] if matches else "",
            severity="medium",
            why='"Not only X but also Y" constructions are heavily overused in AI writing. State the point directly.'
        )]
    return []


def check_hyphenated_pairs(text: str) -> list[PatternMatch]:
    matches = re.findall(HYPHENATED_PAIRS, text, re.IGNORECASE)
    if matches:
        return [PatternMatch(
            pattern_name="Hyphenated Word Pair",
            example=matches[0],
            severity="medium",
            why=f'"{matches[0]}" is a clichéd compound modifier. Find a more specific description.'
        )]
    return []


def check_rule_of_three(text: str) -> list[PatternMatch]:
    # Look for comma-separated lists of exactly three items ending with "and"
    pattern = r'[\w\s]+,\s[\w\s]+,\s(?:and|or)\s[\w\s]+'
    matches = re.findall(pattern, text)
    if len(matches) >= 3:
        return [PatternMatch(
            pattern_name="Rule of Three Overuse",
            example=f"{len(matches)} triple-item lists found",
            severity="low",
            why="Listing exactly three examples every time is a mechanical AI pattern. Use one strong example or vary the count."
        )]
    return []


def check_ing_endings(text: str) -> list[PatternMatch]:
    # Superficial -ing clause tacked onto sentence end
    pattern = r',\s(?:highlighting|underscoring|emphasizing|showcasing|reflecting|symbolizing|fostering|cultivating|ensuring|demonstrating)\s'
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        return [PatternMatch(
            pattern_name="Superficial -ing Ending",
            example=matches[0].strip(),
            severity="high",
            why='Tacking "-ing" clauses onto sentences to add fake depth is a primary AI writing tell. Delete the clause or make it a separate sentence with real content.'
        )]
    return []


# ─── Main Scorer ──────────────────────────────────────────────────────────────

def score_content(text: str) -> HumanizerResult:
    all_patterns = []
    all_patterns.extend(check_banned_words(text))
    all_patterns.extend(check_banned_phrases(text))
    all_patterns.extend(check_hollow_affirmatives(text))
    all_patterns.extend(check_em_dashes(text))
    all_patterns.extend(check_negative_parallelisms(text))
    all_patterns.extend(check_hyphenated_pairs(text))
    all_patterns.extend(check_rule_of_three(text))
    all_patterns.extend(check_ing_endings(text))

    # Score calculation
    high_count = sum(1 for p in all_patterns if p.severity == "high")
    medium_count = sum(1 for p in all_patterns if p.severity == "medium")
    low_count = sum(1 for p in all_patterns if p.severity == "low")

    raw_score = (high_count * 2) + (medium_count * 1) + (low_count * 0.5)
    score = min(10, max(1, round(raw_score + 1)))

    passes = score <= 4

    if score <= 2:
        summary = "Sounds human. Clean."
    elif score <= 4:
        summary = "Mostly human. Minor patterns present."
    elif score <= 6:
        summary = "Mixed. Several AI tells. Needs editing."
    elif score <= 8:
        summary = "Clearly AI-generated. Significant revision needed."
    else:
        summary = "Pure slop. Rewrite from scratch."

    return HumanizerResult(
        score=score,
        patterns_found=all_patterns,
        passes=passes,
        summary=summary
    )


# ─── LLM-Powered Deep Rewrite ─────────────────────────────────────────────────

def deep_rewrite(text: str, voice_document: str, client: anthropic.Anthropic) -> str:
    """
    Uses Claude to do a full humanizer rewrite when pattern score is too high.
    Falls back to original if rewrite fails.
    """
    system = f"""You are a writing editor. Your job is to rewrite AI-generated text to sound like a specific human wrote it.

{voice_document}

Rules for rewriting:
- Remove all AI vocabulary words and phrases
- Vary sentence length and structure
- Add opinions and a point of view
- Use specific examples instead of vague generalisations
- Delete anything that adds no information
- Never use em dashes
- Return ONLY the rewritten text, no explanation"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system,
            messages=[{
                "role": "user",
                "content": f"Rewrite this to sound human:\n\n{text}"
            }]
        )
        return response.content[0].text.strip()
    except Exception:
        return text  # Return original if rewrite fails


# ─── Full Pipeline ────────────────────────────────────────────────────────────

def check_and_rewrite(
    text: str,
    voice_document: str,
    client: anthropic.Anthropic,
    auto_rewrite: bool = True
) -> dict:
    """
    Full pipeline: score, flag, optionally rewrite.
    Returns dict suitable for API response.
    """
    result = score_content(text)

    output = {
        "original": text,
        "score_before": result.score,
        "patterns_found": [
            {
                "pattern": p.pattern_name,
                "example": p.example,
                "severity": p.severity,
                "why": p.why
            }
            for p in result.patterns_found
        ],
        "passes": result.passes,
        "summary": result.summary,
        "rewritten": text,
        "score_after": result.score
    }

    if not result.passes and auto_rewrite:
        rewritten = deep_rewrite(text, voice_document, client)
        rewrite_result = score_content(rewritten)
        output["rewritten"] = rewritten
        output["score_after"] = rewrite_result.score

    return output
