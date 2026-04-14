"""
Performance Tracker: pulls engagement data, logs against post history,
generates weekly performance report, identifies top-performing pillars and formats.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional
import anthropic


POSTS_DIR = "posts"


# ─── Data Logging ─────────────────────────────────────────────────────────────

def log_performance(
    client_id: str,
    post_id: str,
    platform: str,
    likes: int,
    comments: int,
    shares: int,
    impressions: int = 0,
    clicks: int = 0,
    base_path: str = "voices"
) -> dict:
    """
    Logs engagement data against a post record.
    Call this manually or via LinkedIn/X API after posts have been live 24-48 hours.
    """
    post_file = Path(base_path) / client_id / POSTS_DIR / f"{post_id}.json"
    if not post_file.exists():
        raise FileNotFoundError(f"Post not found: {post_id}")

    with open(post_file) as f:
        post = json.load(f)

    # Build performance record
    perf_record = {
        "platform": platform,
        "logged_at": datetime.now().isoformat(),
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "impressions": impressions,
        "clicks": clicks,
        "engagement_rate": round(
            (likes + comments + shares) / max(impressions, 1) * 100, 2
        ),
        "engagement_score": (likes * 1) + (comments * 3) + (shares * 5),
    }

    if "performance" not in post:
        post["performance"] = []
    post["performance"].append(perf_record)
    post["status"] = "published"

    with open(post_file, "w") as f:
        json.dump(post, f, indent=2)

    return perf_record


# ─── Report Generator ─────────────────────────────────────────────────────────

def generate_weekly_report(
    client_id: str,
    base_path: str = "voices",
    days_back: int = 7
) -> dict:
    """
    Analyses post performance over the last N days.
    Returns structured report with top posts, pillar analysis, format analysis.
    """
    posts_dir = Path(base_path) / client_id / POSTS_DIR
    if not posts_dir.exists():
        return {"error": "No posts found"}

    cutoff = datetime.now() - timedelta(days=days_back)
    all_posts = []

    for post_file in posts_dir.glob("*.json"):
        with open(post_file) as f:
            post = json.load(f)

        created = post.get("created_at", "")
        if created:
            try:
                if datetime.fromisoformat(created) < cutoff:
                    continue
            except Exception:
                pass

        if post.get("performance"):
            all_posts.append(post)

    if not all_posts:
        return {
            "period": f"Last {days_back} days",
            "client_id": client_id,
            "posts_tracked": 0,
            "message": "No posts with performance data yet. Log engagement data using log_performance()."
        }

    # Aggregate metrics
    by_format = defaultdict(lambda: {"posts": 0, "total_score": 0, "top_score": 0})
    by_pillar = defaultdict(lambda: {"posts": 0, "total_score": 0})
    by_platform = defaultdict(lambda: {"posts": 0, "total_score": 0, "total_impressions": 0})
    all_scored = []

    for post in all_posts:
        topic = post.get("brief", {}).get("topic", "Unknown")
        fmt = post.get("brief", {}).get("format", "unknown")

        for perf in post.get("performance", []):
            score = perf.get("engagement_score", 0)
            platform = perf.get("platform", "unknown")
            impressions = perf.get("impressions", 0)

            by_format[fmt]["posts"] += 1
            by_format[fmt]["total_score"] += score
            by_format[fmt]["top_score"] = max(by_format[fmt]["top_score"], score)

            by_platform[platform]["posts"] += 1
            by_platform[platform]["total_score"] += score
            by_platform[platform]["total_impressions"] += impressions

            all_scored.append({
                "post_id": post.get("post_id"),
                "topic": topic,
                "format": fmt,
                "platform": platform,
                "score": score,
                "likes": perf.get("likes", 0),
                "comments": perf.get("comments", 0),
                "shares": perf.get("shares", 0),
            })

    # Top posts
    top_posts = sorted(all_scored, key=lambda x: x["score"], reverse=True)[:5]

    # Format performance
    format_summary = []
    for fmt, data in by_format.items():
        avg = data["total_score"] / max(data["posts"], 1)
        format_summary.append({
            "format": fmt,
            "posts": data["posts"],
            "avg_score": round(avg, 1),
            "top_score": data["top_score"]
        })
    format_summary.sort(key=lambda x: x["avg_score"], reverse=True)

    # Platform performance
    platform_summary = []
    for plat, data in by_platform.items():
        avg = data["total_score"] / max(data["posts"], 1)
        platform_summary.append({
            "platform": plat,
            "posts": data["posts"],
            "avg_score": round(avg, 1),
            "total_impressions": data["total_impressions"]
        })

    report = {
        "period": f"Last {days_back} days",
        "generated_at": datetime.now().isoformat(),
        "client_id": client_id,
        "posts_tracked": len(all_posts),
        "top_posts": top_posts,
        "by_format": format_summary,
        "by_platform": platform_summary,
    }

    # Save report
    reports_dir = Path(base_path) / client_id / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    return report


def generate_voice_tuning_brief(
    report: dict,
    api_client: anthropic.Anthropic
) -> str:
    """
    Takes a performance report and generates a voice tuning recommendation.
    This becomes the input for /voice/{client_id}/tune endpoint.
    """
    if report.get("posts_tracked", 0) < 5:
        return "Not enough data yet. Need at least 5 tracked posts for meaningful tuning recommendations."

    report_text = json.dumps(report, indent=2)

    system = """You are a content strategist analysing social media performance data.
Based on the report, generate specific, actionable voice tuning recommendations.
Focus on: which formats to double down on, which topics resonated most, what to change in the voice rules.
Be specific and direct. No vague advice. 3-5 bullet points maximum."""

    response = api_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Generate voice tuning recommendations from this performance data:\n\n{report_text}"
        }]
    )

    return response.content[0].text.strip()


def print_report(report: dict):
    """Pretty-prints a performance report to terminal."""
    print(f"\n{'='*60}")
    print(f"PERFORMANCE REPORT — {report.get('period')}")
    print(f"Client: {report.get('client_id')} | Posts tracked: {report.get('posts_tracked')}")
    print(f"{'='*60}\n")

    if report.get("message"):
        print(report["message"])
        return

    print("TOP POSTS:")
    for i, post in enumerate(report.get("top_posts", [])[:5], 1):
        print(f"  {i}. [{post['format']}] {post['topic'][:50]} — score: {post['score']}")
        print(f"     {post['likes']} likes · {post['comments']} comments · {post['shares']} shares")

    print("\nBY FORMAT:")
    for fmt in report.get("by_format", []):
        print(f"  {fmt['format']}: avg {fmt['avg_score']} · {fmt['posts']} posts")

    print("\nBY PLATFORM:")
    for plat in report.get("by_platform", []):
        imp = f" · {plat['total_impressions']:,} impressions" if plat['total_impressions'] else ""
        print(f"  {plat['platform']}: avg {plat['avg_score']} · {plat['posts']} posts{imp}")

    print()


if __name__ == "__main__":
    import sys
    client_id = sys.argv[1] if len(sys.argv) > 1 else "charubak"

    report = generate_weekly_report(client_id)
    print_report(report)

    if report.get("posts_tracked", 0) >= 5:
        api_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        brief = generate_voice_tuning_brief(report, api_client)
        print("VOICE TUNING RECOMMENDATIONS:")
        print(brief)
