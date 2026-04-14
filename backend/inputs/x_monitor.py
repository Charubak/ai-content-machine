"""
X Monitor: watches for trending content and breaking narratives.
Uses X API v2 search to find relevant tweets and threads.
Feeds high-signal items into the brief queue for narrative hijacking.
Falls back to RSS-based trend detection if X API not configured.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import httpx
import anthropic


X_API_BASE = "https://api.twitter.com/2"

DEFAULT_KEYWORDS = [
    "DeFi marketing",
    "Web3 growth strategy",
    "crypto protocol launch",
    "blockchain marketing",
    "TVL growth",
    "AI marketing tools",
    "founder personal brand",
    "Web3 community growth",
    "protocol adoption",
    "DeFi user acquisition",
]

HIGH_SIGNAL_ACCOUNTS = [
    # Add X handles of founders/analysts in your niche
    # "VitalikButerin", "hasufl", "DegenSpartan"
]


@dataclass
class XItem:
    tweet_id: str
    text: str
    author: str
    url: str
    likes: int
    retweets: int
    replies: int
    published: str
    keyword_matched: str
    item_hash: str = ""
    urgency_score: int = 0
    narrative_angle: str = ""

    def __post_init__(self):
        self.item_hash = hashlib.md5(self.tweet_id.encode()).hexdigest()[:12]

    @property
    def engagement(self):
        return self.likes + (self.retweets * 3) + self.replies


# ─── X API Client ─────────────────────────────────────────────────────────────

class XClient:
    def __init__(self, bearer_token: str = None):
        self.token = bearer_token or os.getenv("X_BEARER_TOKEN")
        if not self.token:
            raise ValueError("X_BEARER_TOKEN not set")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "AIContentMachine/1.0"
        }

    def search_recent(
        self,
        query: str,
        max_results: int = 20,
        hours_back: int = 6
    ) -> list[XItem]:
        """Searches recent tweets for a keyword query."""
        start_time = (datetime.utcnow() - timedelta(hours=hours_back)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        params = {
            "query": f"{query} -is:retweet lang:en",
            "max_results": min(max_results, 100),
            "start_time": start_time,
            "tweet.fields": "public_metrics,created_at,author_id",
            "expansions": "author_id",
            "user.fields": "username",
        }

        try:
            with httpx.Client(timeout=15) as client:
                res = client.get(
                    f"{X_API_BASE}/tweets/search/recent",
                    headers=self.headers,
                    params=params
                )
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            print(f"X API error for '{query}': {e}")
            return []

        tweets = data.get("data", [])
        users = {
            u["id"]: u["username"]
            for u in data.get("includes", {}).get("users", [])
        }

        items = []
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            author_id = tweet.get("author_id", "")
            username = users.get(author_id, "unknown")

            items.append(XItem(
                tweet_id=tweet["id"],
                text=tweet["text"],
                author=username,
                url=f"https://x.com/{username}/status/{tweet['id']}",
                likes=metrics.get("like_count", 0),
                retweets=metrics.get("retweet_count", 0),
                replies=metrics.get("reply_count", 0),
                published=tweet.get("created_at", ""),
                keyword_matched=query
            ))

        return sorted(items, key=lambda x: x.engagement, reverse=True)

    def get_user_timeline(self, username: str, max_results: int = 10) -> list[XItem]:
        """Gets recent tweets from a specific account."""
        try:
            # First get user ID
            with httpx.Client(timeout=10) as client:
                res = client.get(
                    f"{X_API_BASE}/users/by/username/{username}",
                    headers=self.headers
                )
                res.raise_for_status()
                user_id = res.json()["data"]["id"]

            # Then get timeline
            params = {
                "max_results": max_results,
                "tweet.fields": "public_metrics,created_at",
                "exclude": "retweets,replies"
            }
            with httpx.Client(timeout=10) as client:
                res = client.get(
                    f"{X_API_BASE}/users/{user_id}/tweets",
                    headers=self.headers,
                    params=params
                )
                res.raise_for_status()
                tweets = res.json().get("data", [])

            items = []
            for tweet in tweets:
                metrics = tweet.get("public_metrics", {})
                items.append(XItem(
                    tweet_id=tweet["id"],
                    text=tweet["text"],
                    author=username,
                    url=f"https://x.com/{username}/status/{tweet['id']}",
                    likes=metrics.get("like_count", 0),
                    retweets=metrics.get("retweet_count", 0),
                    replies=metrics.get("reply_count", 0),
                    published=tweet.get("created_at", ""),
                    keyword_matched=f"@{username}"
                ))
            return items
        except Exception as e:
            print(f"Timeline error for {username}: {e}")
            return []


# ─── Narrative Scorer ─────────────────────────────────────────────────────────

def score_narrative_items(
    items: list[XItem],
    client_pillars: list[str],
    api_client: anthropic.Anthropic,
    min_engagement: int = 50
) -> list[XItem]:
    """
    Filters by engagement floor and scores narrative hijacking potential.
    """
    # Engagement filter first
    filtered = [i for i in items if i.engagement >= min_engagement]
    if not filtered:
        filtered = sorted(items, key=lambda x: x.engagement, reverse=True)[:5]

    if not filtered:
        return []

    pillars_str = "\n".join(f"- {p}" for p in client_pillars)
    items_text = "\n\n".join([
        f"[{j+1}] @{item.author} ({item.engagement} engagement)\n{item.text[:280]}"
        for j, item in enumerate(filtered[:15])
    ])

    system = """Score these tweets for narrative hijacking opportunity.
Return ONLY valid JSON array:
[{
  "index": 1,
  "urgency_score": 8,
  "narrative_angle": "specific angle to take in response"
}, ...]
urgency_score 1-10: how timely and valuable is this as a hijacking opportunity?"""

    try:
        response = api_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=system,
            messages=[{
                "role": "user",
                "content": f"Content pillars:\n{pillars_str}\n\nScore these:\n\n{items_text}"
            }]
        )
        import re
        raw = response.content[0].text.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        scores = json.loads(raw)

        for score_obj in scores:
            idx = score_obj.get("index", 0) - 1
            if 0 <= idx < len(filtered):
                filtered[idx].urgency_score = score_obj.get("urgency_score", 0)
                filtered[idx].narrative_angle = score_obj.get("narrative_angle", "")

    except Exception as e:
        print(f"Scoring error: {e}")

    return sorted(filtered, key=lambda x: x.urgency_score, reverse=True)


# ─── Queue Writer ─────────────────────────────────────────────────────────────

def add_to_narrative_queue(
    items: list[XItem],
    client_id: str,
    base_path: str = "voices",
    min_urgency: int = 6
) -> int:
    """Saves high-urgency items to narrative queue. Returns count added."""
    queue_dir = Path(base_path) / client_id
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_file = queue_dir / "narrative_queue.json"

    existing = []
    if queue_file.exists():
        with open(queue_file) as f:
            existing = json.load(f)

    existing_hashes = {i.get("item_hash") for i in existing}
    added = 0

    for item in items:
        if item.urgency_score < min_urgency:
            continue
        if item.item_hash in existing_hashes:
            continue

        existing.insert(0, {
            **asdict(item),
            "queue_type": "narrative",
            "status": "pending",
            "added_at": datetime.now().isoformat()
        })
        existing_hashes.add(item.item_hash)
        added += 1

    # Keep last 30
    existing = existing[:30]

    with open(queue_file, "w") as f:
        json.dump(existing, f, indent=2)

    return added


# ─── Fallback: RSS-Based Trend Detection ─────────────────────────────────────

def detect_trends_from_rss(client_pillars: list[str]) -> list[dict]:
    """
    Fallback when X API is not configured.
    Uses RSS items already fetched by rss_monitor and looks for breaking patterns.
    """
    # Check if we have recent RSS items
    try:
        from .rss_monitor import fetch_all_feeds
        items = fetch_all_feeds()
        recent = [i for i in items if i.relevance_score >= 7]
        return [{"title": i.title, "url": i.url, "source": i.source} for i in recent[:5]]
    except Exception:
        return []


# ─── Main Runner ──────────────────────────────────────────────────────────────

def run_x_monitor(
    client_id: str,
    client_pillars: list[str],
    keywords: list[str] = None,
    watch_accounts: list[str] = None,
    base_path: str = "voices"
):
    """
    Full X monitor run. Falls back to RSS if X API not available.
    """
    api_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    kw_list = keywords or DEFAULT_KEYWORDS
    accounts = watch_accounts or HIGH_SIGNAL_ACCOUNTS

    print(f"[{datetime.now().strftime('%H:%M')}] Running X monitor for {client_id}...")

    # Try X API first
    x_token = os.getenv("X_BEARER_TOKEN")
    all_items = []

    if x_token:
        try:
            x_client = XClient(x_token)

            # Search keywords
            for kw in kw_list[:8]:  # Cap to avoid rate limits
                items = x_client.search_recent(kw, max_results=15, hours_back=6)
                all_items.extend(items)

            # Watch specific accounts
            for account in accounts[:5]:
                items = x_client.get_user_timeline(account, max_results=5)
                all_items.extend(items)

            print(f"  Fetched {len(all_items)} tweets via X API")

        except Exception as e:
            print(f"  X API unavailable: {e}")
            print("  Falling back to RSS trend detection")
    else:
        print("  X_BEARER_TOKEN not set — using RSS fallback")

    if not all_items:
        trends = detect_trends_from_rss(client_pillars)
        if trends:
            print(f"  Found {len(trends)} trending RSS items as fallback")
        return

    # Deduplicate
    seen = set()
    unique_items = []
    for item in all_items:
        if item.item_hash not in seen:
            seen.add(item.item_hash)
            unique_items.append(item)

    print(f"  {len(unique_items)} unique items after dedup")

    # Score
    scored = score_narrative_items(unique_items, client_pillars, api_client)
    high_urgency = [i for i in scored if i.urgency_score >= 6]
    print(f"  {len(high_urgency)} items scored 6+ urgency")

    if not high_urgency:
        print("  No high-urgency narrative opportunities")
        return

    # Add to queue
    added = add_to_narrative_queue(high_urgency, client_id, base_path)
    print(f"  Added {added} items to narrative queue")

    for item in high_urgency[:3]:
        icon = "🔴" if item.urgency_score >= 8 else "🟡"
        print(f"  {icon} [{item.urgency_score}/10] @{item.author}: {item.text[:60]}")
        if item.narrative_angle:
            print(f"     Angle: {item.narrative_angle[:80]}")


if __name__ == "__main__":
    import sys
    client_id = sys.argv[1] if len(sys.argv) > 1 else "charubak"
    pillars = [
        "What founders get wrong about growth marketing",
        "DeFi growth tactics that move TVL and users",
        "The real state of Web3 marketing vs the hype",
        "Building AI tools with Python and the Anthropic API",
        "How a mainnet launch actually works"
    ]
    run_x_monitor(client_id, pillars)
