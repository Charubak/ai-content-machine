"""
Voice Builder: generates a structured Voice Document from multiple input sources.
Accepts writing samples (URLs or pasted text), best posts, manual rules, and interview answers.
Outputs a versioned markdown Voice Document ready to use as system prompt.
"""

import re
import json
from datetime import datetime
from pathlib import Path
import anthropic


# ─── Input Models ─────────────────────────────────────────────────────────────

class VoiceIntakeData:
    def __init__(self):
        # Stage 1: Identity
        self.brand_name: str = ""
        self.one_liner: str = ""
        self.target_audience: str = ""
        self.competitor_respect: str = ""
        self.competitor_dislike: str = ""

        # Stage 2: Writing samples
        self.writing_samples: list[str] = []       # Raw text of articles/posts
        self.best_posts: list[dict] = []           # [{text, why_it_worked}]
        self.raw_authentic: list[str] = []         # Unpolished but felt real
        self.content_hate: list[str] = []          # Content they never want to produce

        # Stage 3: Voice rules
        self.tone_position: str = ""               # degen / hybrid / institutional / founder
        self.banned_words: list[str] = []
        self.required_phrases: list[str] = []
        self.owned_topics: list[str] = []
        self.avoided_topics: list[str] = []
        self.always_true: str = ""                 # Free text: always true about content

        # Stage 4: Calibration feedback (from test generation)
        self.calibration_notes: str = ""

        # Metadata
        self.client_id: str = ""
        self.version: int = 1
        self.created_at: str = datetime.now().isoformat()


# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_voice_patterns(samples: list[str], client: anthropic.Anthropic) -> dict:
    """
    Analyses writing samples and extracts concrete voice patterns.
    Returns a dict of observed patterns to embed in the Voice Document.
    """
    if not samples:
        return {}

    combined = "\n\n---\n\n".join(samples[:10])  # Cap at 10 samples

    system = """You are a writing analyst. Analyse the provided writing samples and extract concrete, specific voice patterns.
    
Return ONLY valid JSON with these exact keys:
{
    "sentence_length": "description of typical sentence length patterns",
    "paragraph_structure": "how paragraphs are typically built",
    "opening_style": "how pieces typically open",
    "vocabulary_level": "casual / technical / mixed - with specific examples",
    "verbal_tics": ["list of recurring phrases or constructions"],
    "transition_style": "how the writer moves between ideas",
    "opinion_style": "how the writer states opinions - hedged or direct",
    "specificity": "tendency toward concrete examples vs abstract claims",
    "tone_markers": ["specific words or phrases that define the tone"],
    "what_to_avoid": ["patterns in this writing that should NOT be replicated - weaknesses"]
}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system,
            messages=[{
                "role": "user",
                "content": f"Analyse these writing samples:\n\n{combined}"
            }]
        )
        raw = response.content[0].text.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        return json.loads(raw)
    except Exception:
        return {}


# ─── Voice Document Generator ─────────────────────────────────────────────────

def build_voice_document(intake: VoiceIntakeData, client: anthropic.Anthropic) -> str:
    """
    Takes completed intake data, analyses samples, generates full Voice Document.
    """

    # Analyse writing samples if provided
    all_samples = intake.writing_samples + intake.raw_authentic
    best_post_texts = [p["text"] for p in intake.best_posts]
    all_samples.extend(best_post_texts)

    patterns = {}
    if all_samples:
        patterns = extract_voice_patterns(all_samples, client)

    # Build best posts reference section
    best_posts_section = ""
    if intake.best_posts:
        best_posts_section = "\n## BEST PERFORMING POSTS (reference for tone and structure)\n\n"
        for i, post in enumerate(intake.best_posts[:5], 1):
            best_posts_section += f"**Post {i}**"
            if post.get("why_it_worked"):
                best_posts_section += f" — Why it worked: {post['why_it_worked']}"
            best_posts_section += f"\n\n{post['text'][:500]}{'...' if len(post['text']) > 500 else ''}\n\n"

    # Build patterns section
    patterns_section = ""
    if patterns:
        patterns_section = "\n## OBSERVED VOICE PATTERNS (extracted from writing samples)\n\n"
        if patterns.get("sentence_length"):
            patterns_section += f"**Sentence length:** {patterns['sentence_length']}\n\n"
        if patterns.get("opening_style"):
            patterns_section += f"**Opening style:** {patterns['opening_style']}\n\n"
        if patterns.get("opinion_style"):
            patterns_section += f"**Opinion style:** {patterns['opinion_style']}\n\n"
        if patterns.get("verbal_tics"):
            tics = ", ".join(patterns["verbal_tics"][:8])
            patterns_section += f"**Verbal tics and recurring patterns:** {tics}\n\n"
        if patterns.get("tone_markers"):
            markers = ", ".join(patterns["tone_markers"][:8])
            patterns_section += f"**Tone markers:** {markers}\n\n"
        if patterns.get("what_to_avoid"):
            avoid = ", ".join(patterns["what_to_avoid"][:5])
            patterns_section += f"**Weaknesses to avoid replicating:** {avoid}\n\n"

    # Build banned words section
    all_banned = [
        "delve", "tapestry", "vibrant", "pivotal", "landscape", "underscore",
        "testament", "interplay", "foster", "cultivate", "showcase", "synergy",
        "robust", "seamless", "cutting-edge", "game-changing", "groundbreaking",
        "transformative", "innovative", "holistic", "actionable", "streamline",
        "empower", "dynamic", "paradigm"
    ]
    if intake.banned_words:
        all_banned.extend(intake.banned_words)
    banned_str = ", ".join(sorted(set(all_banned)))

    # Build content never section
    content_hate_section = ""
    if intake.content_hate:
        content_hate_section = "\n## CONTENT TO NEVER PRODUCE\n\n"
        for item in intake.content_hate:
            content_hate_section += f"- {item}\n"

    # Build always true section
    always_true_section = ""
    if intake.always_true:
        always_true_section = f"\n## ALWAYS TRUE ABOUT THIS CONTENT\n\n{intake.always_true}\n"

    # Build calibration section
    calibration_section = ""
    if intake.calibration_notes:
        calibration_section = f"\n## CALIBRATION NOTES\n\n{intake.calibration_notes}\n"

    # Tone description
    tone_descriptions = {
        "degen": "Sharp, irreverent, crypto-native, willing to be provocative. Comfortable with CT humour. Doesn't perform professionalism.",
        "hybrid": "Technical credibility with accessible delivery. Mostly serious with occasional dry humour. Respects the reader's intelligence. Never trying to be edgy.",
        "institutional": "Authoritative, clean, measured. Closer to how Ethereum Foundation or a serious research firm writes. Precision over personality.",
        "founder": "Direct, opinionated, shows the work. No corporate polish. Talks like a builder explaining something to another builder."
    }
    tone_desc = tone_descriptions.get(intake.tone_position, tone_descriptions["hybrid"])

    # Assemble document
    doc = f"""# Voice Document: {intake.brand_name}
## Version {intake.version} — Generated {intake.created_at[:10]}

---

## IDENTITY

**Brand:** {intake.brand_name}
**What they do:** {intake.one_liner}
**Target audience:** {intake.target_audience}

---

## TONE PROFILE

**Position:** {intake.tone_position.title() if intake.tone_position else "Hybrid"}

{tone_desc}

---

## CONTENT PILLARS

Topics this brand owns and posts about with authority:
{chr(10).join(f"- {topic}" for topic in intake.owned_topics) if intake.owned_topics else "- (to be defined)"}

Topics to avoid:
{chr(10).join(f"- {topic}" for topic in intake.avoided_topics) if intake.avoided_topics else "- None specified"}
{patterns_section}{best_posts_section}
---

## VOICE RULES

### Banned words (never use):
{banned_str}

### Banned phrases (never use):
- "In today's rapidly evolving..."
- "It's worth noting that..."
- "At the end of the day..."
- "In conclusion..." / "To summarise..."
- "It goes without saying..."
- Any hollow affirmative opener: "Certainly!", "Absolutely!", "Great question!"

### Required phrases / terminology:
{chr(10).join(f"- {phrase}" for phrase in intake.required_phrases) if intake.required_phrases else "- None specified"}
{always_true_section}
---

## FORMAT RULES

- No em dashes anywhere — use commas, colons, or restructure
- No bullet point lists on social unless each point is substantive
- No headers inside social posts
- Short opener to hook, then develop the idea with depth
- Vary sentence length: short for emphasis, longer to build argument
- End with a specific takeaway or open observation — not a CTA
- Bring one strong specific example rather than listing three vague ones
{content_hate_section}
---

## FAILURE CONDITIONS

A post has failed if:
- Someone could remove the name and attribute it to any brand in this space
- It reads like a press release or announcement
- It sounds like it was written to impress rather than to be useful
- It uses any banned word or phrase above
- It lectures or moralises
- It states the obvious and presents it as insight
{calibration_section}
---

## REFERENCE CONTENT

Competitor they respect (study their tone, do not copy): {intake.competitor_respect or "Not specified"}
Competitor they dislike (avoid this register entirely): {intake.competitor_dislike or "Not specified"}
"""

    return doc.strip()


# ─── File Management ──────────────────────────────────────────────────────────

def save_voice_document(
    voice_doc: str,
    client_id: str,
    version: int,
    base_path: str = "voices"
) -> str:
    """
    Saves Voice Document to client folder with version number.
    Returns the file path.
    """
    client_dir = Path(base_path) / client_id
    client_dir.mkdir(parents=True, exist_ok=True)
    samples_dir = client_dir / "samples"
    samples_dir.mkdir(exist_ok=True)
    posts_dir = client_dir / "posts"
    posts_dir.mkdir(exist_ok=True)

    filename = f"voice_v{version}.md"
    filepath = client_dir / filename

    with open(filepath, "w") as f:
        f.write(voice_doc)

    return str(filepath)


def load_voice_document(client_id: str, version: int = None, base_path: str = "voices") -> str:
    """
    Loads a Voice Document. If version not specified, loads latest.
    """
    client_dir = Path(base_path) / client_id

    if version:
        filepath = client_dir / f"voice_v{version}.md"
    else:
        # Find latest version
        docs = sorted(client_dir.glob("voice_v*.md"))
        if not docs:
            raise FileNotFoundError(f"No voice document found for client: {client_id}")
        filepath = docs[-1]

    with open(filepath) as f:
        return f.read()


def list_versions(client_id: str, base_path: str = "voices") -> list[int]:
    """Returns list of available version numbers for a client."""
    client_dir = Path(base_path) / client_id
    docs = sorted(client_dir.glob("voice_v*.md"))
    versions = []
    for doc in docs:
        match = re.search(r'voice_v(\d+)\.md', doc.name)
        if match:
            versions.append(int(match.group(1)))
    return versions
