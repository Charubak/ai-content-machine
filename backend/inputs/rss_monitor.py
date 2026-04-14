"""
Input Aggregator: RSS monitor + narrative watcher.
Polls feeds, scores relevance, outputs to brief queue.
Run as a cron job or scheduled task.
"""

import os
import json
import hashlib
import feedparser
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import anthropic


# ─── Default Feed Config ──────────────────────────────────────────────────────

DEFAULT_FEEDS = {
    "web3_growth": [
        "https://thedefiant.io/feed",
        "https://rekt.news/feed",
        "https://blockworks.co/feed",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
    ],
    "ai_marketing": [
        "https://www.marketingbrew.com/feed",
        "https://chiefmartec.com/feed/",
        "https://www.searchenginejournal.com/feed/",
    ],
    "ai_tools": [
        "https://simonwillison.net/atom/everything/",
        "https://www.bensbites.com/feed",
    ]
}

DEFAULT_KEYWORDS = [
    "DeFi marketing", "Web3 growth", "crypto marketing",
    "protocol launch", "TVL growth", "token launch marketing",
    "AI marketing tools", "content automation", "growth marketing",
    "founder personal brand", "B2B content", "LinkedIn growth"
]


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class FeedItem:
    title: str
    url: str
    summary: str
    source: str
    published: str
    relevance_score: int = 0
    relevance_reason: str = ""
    item_hash: str = ""

    def __post_init__(self):
        self.item_hash = hashlib.md5(self.url.encode()).hexdigest()[:12]


@dataclass
class BriefSuggestion:
    source_item: FeedItem
    suggested_angle: str
    suggested_format: str
    urgency: str  # "high" (narrative opportunity), "normal", "low"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# ─── Feed Fetcher ─────────────────────────────────────────────────────────────

def fetch_feed(url: str, max_items: int = 10) -> list[FeedItem]:
    """Fetches and parses an RSS feed, returns recent items."""
    try:
        feed = feedparser.parse(url)
        items = []
        cutoff = datetime.now() - timedelta(hours=48)

        for entry in feed.entries[:max_items]:
            # Parse publish date
            published = ""
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    pub_dt = datetime(*entry.published_parsed[:6])
                    if pub_dt < cutoff:
                        continue
                    published = pub_dt.isoformat()
                except Exception:
                    published = entry.get('published', '')
            else:
                published = entry.get('published', '')

            summary = entry.get('summary', '') or entry.get('description', '')
            # Strip HTML
            summary = summary.replace('<p>', '').replace('</p>', ' ')
            summary = summary.replace('<br>', ' ').replace('<br/>', ' ')
            import re
            summary = re.sub(r'<[^>]+>', '', summary)[:500]

            items.append(FeedItem(
                title=entry.get('title', ''),
                url=entry.get('link', ''),
                summary=summary,
                source=feed.feed.get('title', url),
                published=published
            ))

        return items
    except Exception as e:
        print(f"Feed fetch error for {url}: {e}")
        return []


def fetch_all_feeds(feed_config: dict = None) -> list[FeedItem]:
    """Fetches all configured feeds and returns deduplicated items."""
    config = feed_config or DEFAULT_FEEDS
    all_items = []
    seen_hashes = set()

    for category, urls in config.items():
        for url in urls:
            items = fetch_feed(url)
            for item in items:
                if item.item_hash not in seen_hashes:
                    seen_hashes.add(item.item_hash)
                    all_items.append(item)

    return all_items


# ─── Relevance Scoring ────────────────────────────────────────────────────────

def score_relevance(
    items: list[FeedItem],
    client_pillars: list[str],
    api_client: anthropic.Anthropic,
    batch_size: int = 10
) -> list[FeedItem]:
    """
    Scores feed items for relevance to content pillars.
    Uses Claude for nuanced relevance scoring in batches.
    """
    if not items:
        return []

    pillars_str = "\n".join(f"- {p}" for p in client_pillars)
    scored_items = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        items_text = "\n\n".join([
            f"[{j+1}] {item.title}\n{item.summary[:200]}"
            for j, item in enumerate(batch)
        ])

        system = """You score news items for content relevance.
Return ONLY valid JSON array with one object per item:
[{"index": 1, "score": 8, "reason": "directly about DeFi protocol growth"}, ...]
Score 1-10: 1=totally irrelevant, 10=perfect content opportunity"""

        try:
            response = api_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                system=system,
                messages=[{
                    "role": "user",
                    "content": f"Content pillars:\n{pillars_str}\n\nScore these items:\n\n{items_text}"
                }]
            )
            raw = response.content[0].text.strip()
            import re
            raw = re.sub(r'```json|```', '', raw).strip()
            scores = json.loads(raw)

            for score_obj in scores:
                idx = score_obj.get("index", 0) - 1
                if 0 <= idx < len(batch):
                    batch[idx].relevance_score = score_obj.get("score", 0)
                    batch[idx].relevance_reason = score_obj.get("reason", "")

        except Exception as e:
            print(f"Scoring error: {e}")

        scored_items.extend(batch)

    return sorted(scored_items, key=lambda x: x.relevance_score, reverse=True)


# ─── Brief Generator ──────────────────────────────────────────────────────────

def generate_brief_suggestions(
    items: list[FeedItem],
    client_pillars: list[str],
    api_client: anthropic.Anthropic,
    min_relevance: int = 6,
    max_suggestions: int = 5
) -> list[BriefSuggestion]:
    """
    Takes high-relevance items and generates content brief suggestions.
    """
    relevant = [item for item in items if item.relevance_score >= min_relevance][:max_suggestions]
    if not relevant:
        return []

    pillars_str = "\n".join(f"- {p}" for p in client_pillars)
    items_text = "\n\n".join([
        f"[{j+1}] Score: {item.relevance_score}/10\nTitle: {item.title}\nSummary: {item.summary[:300]}"
        for j, item in enumerate(relevant)
    ])

    system = """Generate content brief suggestions from news items.
Return ONLY valid JSON array:
[{
  "index": 1,
  "angle": "specific content angle to take on this item",
  "format": "opinion|reaction|experience|narrative",
  "urgency": "high|normal|low"
}, ...]"""

    try:
        response = api_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=system,
            messages=[{
                "role": "user",
                "content": f"Content pillars:\n{pillars_str}\n\nGenerate briefs for:\n\n{items_text}"
            }]
        )
        raw = response.content[0].text.strip()
        import re
        raw = re.sub(r'```json|```', '', raw).strip()
        suggestions_data = json.loads(raw)

        suggestions = []
        for s in suggestions_data:
            idx = s.get("index", 0) - 1
            if 0 <= idx < len(relevant):
                suggestions.append(BriefSuggestion(
                    source_item=relevant[idx],
                    suggested_angle=s.get("angle", ""),
                    suggested_format=s.get("format", "opinion"),
                    urgency=s.get("urgency", "normal")
                ))

        return sorted(suggestions, key=lambda x: {"high": 0, "normal": 1, "low": 2}[x.urgency])

    except Exception as e:
        print(f"Brief generation error: {e}")
        return []


# ─── Queue Management ─────────────────────────────────────────────────────────

def save_brief_queue(
    suggestions: list[BriefSuggestion],
    client_id: str,
    base_path: str = "voices"
) -> str:
    """Saves brief suggestions to client's queue file."""
    queue_dir = Path(base_path) / client_id
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_file = queue_dir / "brief_queue.json"

    # Load existing queue
    existing = []
    if queue_file.exists():
        with open(queue_file) as f:
            existing = json.load(f)

    # Add new suggestions, avoid duplicates by URL
    existing_urls = {s.get("source_item", {}).get("url") for s in existing}
    new_items = []
    for s in suggestions:
        if s.source_item.url not in existing_urls:
            new_items.append({
                "source_item": asdict(s.source_item),
                "suggested_angle": s.suggested_angle,
                "suggested_format": s.suggested_format,
                "urgency": s.urgency,
                "created_at": s.created_at,
                "status": "pending"
            })

    combined = new_items + existing
    # Keep last 50 items
    combined = combined[:50]

    with open(queue_file, "w") as f:
        json.dump(combined, f, indent=2)

    return str(queue_file)


def load_brief_queue(client_id: str, base_path: str = "voices") -> list[dict]:
    """Loads the brief queue for a client."""
    queue_file = Path(base_path) / client_id / "brief_queue.json"
    if not queue_file.exists():
        return []
    with open(queue_file) as f:
        return json.load(f)


# ─── Main Runner ──────────────────────────────────────────────────────────────

def run_monitor(
    client_id: str,
    client_pillars: list[str],
    feed_config: dict = None,
    base_path: str = "voices"
):
    """
    Full monitor run: fetch feeds, score, generate briefs, save to queue.
    Run this on a schedule (cron, APScheduler, etc.)
    """
    api_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print(f"[{datetime.now().strftime('%H:%M')}] Running monitor for {client_id}...")

    # Fetch
    items = fetch_all_feeds(feed_config)
    print(f"  Fetched {len(items)} items from feeds")

    if not items:
        print("  No items found")
        return

    # Score
    scored = score_relevance(items, client_pillars, api_client)
    high_relevance = [i for i in scored if i.relevance_score >= 6]
    print(f"  {len(high_relevance)} items scored 6+")

    if not high_relevance:
        print("  Nothing relevant enough for briefs")
        return

    # Generate briefs
    suggestions = generate_brief_suggestions(high_relevance, client_pillars, api_client)
    print(f"  Generated {len(suggestions)} brief suggestions")

    # Save to queue
    queue_path = save_brief_queue(suggestions, client_id, base_path)
    print(f"  Saved to: {queue_path}")

    # Print summary
    for s in suggestions:
        urgency_icon = "🔴" if s.urgency == "high" else "🟡" if s.urgency == "normal" else "🟢"
        print(f"  {urgency_icon} [{s.suggested_format}] {s.source_item.title[:60]}")
        print(f"     Angle: {s.suggested_angle[:80]}")


if __name__ == "__main__":
    # Example usage
    import sys
    client_id = sys.argv[1] if len(sys.argv) > 1 else "charubak"
    pillars = [
        "What founders get wrong about growth marketing",
        "DeFi growth tactics that move TVL and users",
        "The real state of Web3 marketing vs the hype",
        "Building AI tools with Python and the Anthropic API",
        "How a mainnet launch actually works"
    ]
    run_monitor(client_id, pillars)
