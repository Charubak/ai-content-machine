"""
Buffer Publisher: schedules approved posts via Buffer API.
Supports LinkedIn and X/Twitter profiles.
Run manually or triggered from post approval webhook.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import httpx


BUFFER_API_BASE = "https://api.bufferapp.com/1"
POSTS_DIR = "posts"


# ─── Buffer Client ────────────────────────────────────────────────────────────

class BufferClient:
    def __init__(self, access_token: str = None):
        self.token = access_token or os.getenv("BUFFER_ACCESS_TOKEN")
        if not self.token:
            raise ValueError("BUFFER_ACCESS_TOKEN not set")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def get_profiles(self) -> list[dict]:
        """Returns all connected social profiles."""
        with httpx.Client() as client:
            res = client.get(
                f"{BUFFER_API_BASE}/profiles.json",
                headers=self.headers
            )
            res.raise_for_status()
            return res.json()

    def get_profile_ids(self) -> dict:
        """Returns dict of service_type -> profile_id for connected accounts."""
        profiles = self.get_profiles()
        result = {}
        for p in profiles:
            service = p.get("service", "")
            if service in ("linkedin", "twitter"):
                result[service] = p.get("id")
        return result

    def schedule_post(
        self,
        profile_id: str,
        text: str,
        scheduled_at: Optional[str] = None,
        now: bool = False
    ) -> dict:
        """
        Schedules a post to a Buffer profile.
        scheduled_at: ISO format datetime string
        now: if True, publishes immediately (goes to top of queue)
        """
        payload = {
            "profile_ids[]": profile_id,
            "text": text,
        }

        if now:
            payload["now"] = "true"
        elif scheduled_at:
            # Buffer expects Unix timestamp
            try:
                dt = datetime.fromisoformat(scheduled_at)
                payload["scheduled_at"] = str(int(dt.timestamp()))
            except Exception:
                pass

        with httpx.Client() as client:
            res = client.post(
                f"{BUFFER_API_BASE}/updates/create.json",
                headers=self.headers,
                data=payload
            )
            res.raise_for_status()
            return res.json()

    def get_pending_updates(self, profile_id: str) -> list[dict]:
        """Returns pending scheduled updates for a profile."""
        with httpx.Client() as client:
            res = client.get(
                f"{BUFFER_API_BASE}/profiles/{profile_id}/updates/pending.json",
                headers=self.headers
            )
            res.raise_for_status()
            return res.json().get("updates", [])


# ─── Scheduling Logic ─────────────────────────────────────────────────────────

PLATFORM_VARIANT_MAP = {
    "linkedin": "linkedin_long",
    "linkedin_short": "linkedin_short",
    "twitter": "x_single",
    "x_thread": "x_thread",
}

OPTIMAL_TIMES = {
    "linkedin": ["08:30", "12:00", "17:30"],
    "twitter": ["09:00", "12:30", "18:00", "21:00"],
}


def get_next_slot(service: str, existing_slots: list[str]) -> str:
    """
    Returns next available posting slot for a service.
    Spreads posts across optimal times, avoiding clashes.
    """
    times = OPTIMAL_TIMES.get(service, ["10:00", "16:00"])
    now = datetime.now()

    for days_ahead in range(7):
        target_date = now + timedelta(days=days_ahead)
        for time_str in times:
            hour, minute = map(int, time_str.split(":"))
            slot = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if slot <= now:
                continue

            slot_iso = slot.isoformat()
            if slot_iso not in existing_slots:
                return slot_iso

    # Fallback: 24 hours from now
    return (now + timedelta(hours=24)).isoformat()


def schedule_approved_post(
    post_id: str,
    client_id: str,
    platforms: list[str] = None,
    base_path: str = "voices"
) -> dict:
    """
    Finds an approved post and schedules it to Buffer.
    platforms: list of "linkedin", "twitter" — defaults to both
    """
    if platforms is None:
        platforms = ["linkedin", "twitter"]

    post_file = Path(base_path) / client_id / POSTS_DIR / f"{post_id}.json"
    if not post_file.exists():
        raise FileNotFoundError(f"Post not found: {post_id}")

    with open(post_file) as f:
        post = json.load(f)

    if post.get("status") != "approved":
        raise ValueError(f"Post {post_id} is not approved (status: {post.get('status')})")

    try:
        buffer = BufferClient()
        profile_ids = buffer.get_profile_ids()
    except Exception as e:
        return {"error": str(e), "note": "Buffer not configured — post approved but not scheduled"}

    results = []
    output = post.get("output", {})

    for platform in platforms:
        profile_id = profile_ids.get(platform)
        if not profile_id:
            results.append({"platform": platform, "status": "skipped", "reason": "no profile connected"})
            continue

        # Get content for platform
        if platform == "linkedin":
            text = output.get("linkedin_long") or output.get("linkedin_short", "")
        elif platform == "twitter":
            # For X: check if thread or single
            thread = output.get("x_thread", [])
            if thread and len(thread) > 1:
                # Buffer doesn't natively support threads via API
                # Schedule first tweet, rest as replies (workaround)
                text = thread[0]
            else:
                text = output.get("x_single", "")

        if not text:
            results.append({"platform": platform, "status": "skipped", "reason": "no content"})
            continue

        # Get existing slots to avoid clashes
        try:
            pending = buffer.get_pending_updates(profile_id)
            existing_slots = [u.get("scheduled_at", "") for u in pending]
        except Exception:
            existing_slots = []

        scheduled_at = get_next_slot(platform, existing_slots)

        try:
            result = buffer.schedule_post(profile_id, text, scheduled_at=scheduled_at)
            results.append({
                "platform": platform,
                "status": "scheduled",
                "scheduled_at": scheduled_at,
                "buffer_id": result.get("updates", [{}])[0].get("id")
            })
        except Exception as e:
            results.append({"platform": platform, "status": "error", "error": str(e)})

    # Update post file with scheduling results
    post["scheduled"] = results
    post["status"] = "scheduled"
    post["scheduled_at"] = datetime.now().isoformat()
    with open(post_file, "w") as f:
        json.dump(post, f, indent=2)

    return {"post_id": post_id, "results": results}


def schedule_all_approved(client_id: str, base_path: str = "voices") -> list[dict]:
    """Batch schedules all approved posts for a client."""
    posts_dir = Path(base_path) / client_id / POSTS_DIR
    if not posts_dir.exists():
        return []

    results = []
    for post_file in sorted(posts_dir.glob("*.json")):
        with open(post_file) as f:
            post = json.load(f)
        if post.get("status") == "approved":
            try:
                result = schedule_approved_post(
                    post["post_id"], client_id, base_path=base_path
                )
                results.append(result)
            except Exception as e:
                results.append({"post_id": post.get("post_id"), "error": str(e)})

    return results


if __name__ == "__main__":
    import sys
    client_id = sys.argv[1] if len(sys.argv) > 1 else "charubak"
    print(f"Scheduling all approved posts for {client_id}...")
    results = schedule_all_approved(client_id)
    for r in results:
        print(json.dumps(r, indent=2))
