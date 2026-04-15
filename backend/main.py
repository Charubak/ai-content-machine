"""
FastAPI backend for AI Content Machine.
Exposes endpoints for demo, onboarding, generation, review, and performance.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

from agents.content_agent import ContentBrief, ContentFormat, generate_content, generate_reaction
from agents.voice_builder import (
    VoiceIntakeData, build_voice_document,
    save_voice_document, load_voice_document, list_versions
)
from agents.humanizer import check_and_rewrite

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Content Machine",
    description="Automated content generation with voice calibration and quality gate",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICES_PATH = os.getenv("VOICES_PATH", "voices")
POSTS_DIR = "posts"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ─── Request / Response Models ────────────────────────────────────────────────

class DemoRequest(BaseModel):
    raw_thought: str
    tone: str = "hybrid"  # degen / hybrid / institutional / founder


class DemoResponse(BaseModel):
    linkedin_long: str
    linkedin_short: str
    x_thread: list[str]
    x_single: str
    score_before: int
    score_after: int


class OnboardingRequest(BaseModel):
    brand_name: str
    one_liner: str
    target_audience: str
    tone_position: str
    owned_topics: list[str]
    avoided_topics: list[str] = []
    banned_words: list[str] = []
    required_phrases: list[str] = []
    always_true: str = ""
    competitor_respect: str = ""
    competitor_dislike: str = ""
    writing_samples: list[str] = []
    best_posts: list[dict] = []
    content_hate: list[str] = []
    calibration_notes: str = ""
    client_id: str = ""


class OnboardingResponse(BaseModel):
    client_id: str
    version: int
    voice_document: str
    saved_path: str


class GenerateRequest(BaseModel):
    client_id: str
    topic: str
    angle: str
    format: str = "opinion"
    credential: str = ""
    data_point: str = ""
    source_url: str = ""
    source_text: str = ""
    platform_priority: str = "both"
    company_voice: bool = False
    voice_version: Optional[int] = None


class GenerateResponse(BaseModel):
    linkedin_long: str
    linkedin_short: str
    x_thread: list[str]
    x_single: str
    community_message: str
    scores: dict
    passed_gate: bool
    post_id: str


class ReactionRequest(BaseModel):
    client_id: str
    narrative_text: str
    narrative_source: str = "Unknown source"


class HumanizerRequest(BaseModel):
    text: str
    client_id: str = ""
    auto_rewrite: bool = True


class UpdateVoiceRequest(BaseModel):
    client_id: str
    calibration_notes: str = ""
    additional_banned_words: list[str] = []
    performance_insights: str = ""


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# --- Demo endpoint (no auth, no client ID needed) ---

@app.post("/demo", response_model=DemoResponse)
def demo_generate(req: DemoRequest):
    """
    Public demo endpoint. Generates content from a raw thought using a
    built-in demo voice. No client setup required.
    """
    demo_voice_path = Path(VOICES_PATH) / "demo"
    demo_voice_path.mkdir(parents=True, exist_ok=True)
    demo_voice_file = demo_voice_path / "voice_v1.md"

    # Use Charubak's voice doc as the demo, or a generic one if not found
    if not demo_voice_file.exists():
        # Write a generic but good demo voice doc
        demo_voice = f"""# Voice Document: Demo
## Version 1

## IDENTITY
A senior Web3/AI growth marketer who builds AI tools and has run protocol launches.

## TONE PROFILE
Position: {req.tone.title()}
Direct, technical credibility, accessible delivery. Has opinions. Shows the work.

## VOICE RULES
Banned words: delve, tapestry, vibrant, pivotal, leverage, synergy, robust, seamless, groundbreaking, transformative, stakeholders, cultivate, showcase, foster, innovative, cutting-edge
No em dashes. No hollow affirmatives. No filler phrases.
Short hook opener, then develop with depth. Specific examples over vague generalisations.

## FORMAT RULES
LinkedIn long: 600-900 words, no headers, no bullets, continuous argument
LinkedIn short: 150-250 words, one sharp observation
X thread: tweet 1 standalone hook, 8 tweets, specific numbers in 3 middle tweets
X single: under 240 chars, no hashtags"""
        with open(demo_voice_file, "w") as f:
            f.write(demo_voice)

    brief = ContentBrief(
        client_id="demo",
        topic=req.raw_thought[:100],
        angle=req.raw_thought,
        format=ContentFormat.OPINION,
        voices_path=VOICES_PATH
    )

    try:
        output = generate_content(brief, client, auto_rewrite=True)
        avg_score_before = sum(
            v["before"] for v in output.scores.values()
        ) // max(len(output.scores), 1)
        avg_score_after = sum(
            v["after"] for v in output.scores.values()
        ) // max(len(output.scores), 1)

        return DemoResponse(
            linkedin_long=output.linkedin_long,
            linkedin_short=output.linkedin_short,
            x_thread=output.x_thread,
            x_single=output.x_single,
            score_before=avg_score_before,
            score_after=avg_score_after
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Onboarding ---

@app.post("/onboard", response_model=OnboardingResponse)
def onboard_client(req: OnboardingRequest):
    """
    Creates a new client Voice Document from intake data and writing samples.
    """
    intake = VoiceIntakeData()
    intake.brand_name = req.brand_name
    intake.one_liner = req.one_liner
    intake.target_audience = req.target_audience
    intake.tone_position = req.tone_position
    intake.owned_topics = req.owned_topics
    intake.avoided_topics = req.avoided_topics
    intake.banned_words = req.banned_words
    intake.required_phrases = req.required_phrases
    intake.always_true = req.always_true
    intake.competitor_respect = req.competitor_respect
    intake.competitor_dislike = req.competitor_dislike
    intake.writing_samples = req.writing_samples
    intake.best_posts = req.best_posts
    intake.content_hate = req.content_hate
    intake.calibration_notes = req.calibration_notes

    client_id = req.client_id or f"client_{uuid.uuid4().hex[:8]}"
    intake.client_id = client_id

    # Check if client exists, set version
    existing_versions = list_versions(client_id, base_path=VOICES_PATH)
    intake.version = max(existing_versions, default=0) + 1

    try:
        voice_doc = build_voice_document(intake, client)
        saved_path = save_voice_document(voice_doc, client_id, intake.version, VOICES_PATH)

        return OnboardingResponse(
            client_id=client_id,
            version=intake.version,
            voice_document=voice_doc,
            saved_path=saved_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Content Generation ---

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """
    Generates content from a brief using the client's Voice Document.
    """
    try:
        format_map = {
            "opinion": ContentFormat.OPINION,
            "reaction": ContentFormat.REACTION,
            "experience": ContentFormat.EXPERIENCE,
            "data": ContentFormat.DATA,
            "narrative": ContentFormat.NARRATIVE
        }

        brief = ContentBrief(
            client_id=req.client_id,
            topic=req.topic,
            angle=req.angle,
            format=format_map.get(req.format, ContentFormat.OPINION),
            credential=req.credential,
            data_point=req.data_point,
            source_url=req.source_url,
            source_text=req.source_text,
            platform_priority=req.platform_priority,
            company_voice=req.company_voice,
            voice_version=req.voice_version,
            voices_path=VOICES_PATH
        )

        output = generate_content(brief, client, auto_rewrite=True)

        # Save post to client history
        post_id = f"post_{uuid.uuid4().hex[:8]}"
        post_data = {
            "post_id": post_id,
            "client_id": req.client_id,
            "brief": req.dict(),
            "output": {
                "linkedin_long": output.linkedin_long,
                "linkedin_short": output.linkedin_short,
                "x_thread": output.x_thread,
                "x_single": output.x_single,
                "community_message": output.community_message
            },
            "scores": output.scores,
            "passed_gate": output.passed_gate,
            "status": "pending_review",
            "created_at": datetime.now().isoformat()
        }

        posts_dir = Path(VOICES_PATH) / req.client_id / POSTS_DIR
        posts_dir.mkdir(parents=True, exist_ok=True)
        with open(posts_dir / f"{post_id}.json", "w") as f:
            json.dump(post_data, f, indent=2)

        return GenerateResponse(
            linkedin_long=output.linkedin_long,
            linkedin_short=output.linkedin_short,
            x_thread=output.x_thread,
            x_single=output.x_single,
            community_message=output.community_message,
            scores=output.scores,
            passed_gate=output.passed_gate,
            post_id=post_id
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No voice document found for client: {req.client_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Narrative Fast-Path ---

@app.post("/react")
def react_to_narrative(req: ReactionRequest):
    """
    Fast-path for narrative hijacking. Returns reaction posts quickly.
    """
    try:
        result = generate_reaction(
            req.client_id,
            req.narrative_text,
            req.narrative_source,
            client,
            voices_path=VOICES_PATH
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No voice document found for client: {req.client_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Humanizer standalone ---

@app.post("/humanize")
def humanize(req: HumanizerRequest):
    """
    Runs the humanizer quality gate on any text.
    Optionally uses a client Voice Document for targeted rewriting.
    """
    voice_doc = ""
    if req.client_id:
        try:
            voice_doc = load_voice_document(req.client_id, base_path=VOICES_PATH)
        except FileNotFoundError:
            pass  # Use generic rewrite if no voice doc

    result = check_and_rewrite(req.text, voice_doc, client, req.auto_rewrite)
    return result


# --- Post queue ---

@app.get("/posts/{client_id}")
def get_posts(client_id: str, status: str = None):
    """
    Returns post history for a client. Optionally filter by status.
    """
    posts_dir = Path(VOICES_PATH) / client_id / POSTS_DIR
    if not posts_dir.exists():
        return {"posts": []}

    posts = []
    for post_file in sorted(posts_dir.glob("*.json"), reverse=True):
        with open(post_file) as f:
            post = json.load(f)
        if status is None or post.get("status") == status:
            posts.append(post)

    return {"posts": posts, "total": len(posts)}


@app.patch("/posts/{client_id}/{post_id}")
def update_post_status(client_id: str, post_id: str, status: str, notes: str = ""):
    """
    Updates post status: pending_review → approved / rejected / published
    """
    post_file = Path(VOICES_PATH) / client_id / POSTS_DIR / f"{post_id}.json"
    if not post_file.exists():
        raise HTTPException(status_code=404, detail="Post not found")

    with open(post_file) as f:
        post = json.load(f)

    post["status"] = status
    post["reviewed_at"] = datetime.now().isoformat()
    if notes:
        post["review_notes"] = notes

    with open(post_file, "w") as f:
        json.dump(post, f, indent=2)

    return {"post_id": post_id, "status": status}


# --- Voice management ---

@app.get("/voice/{client_id}")
def get_voice(client_id: str, version: int = None):
    """Returns the Voice Document for a client."""
    try:
        doc = load_voice_document(client_id, version=version, base_path=VOICES_PATH)
        versions = list_versions(client_id, base_path=VOICES_PATH)
        return {
            "client_id": client_id,
            "current_version": version or max(versions),
            "available_versions": versions,
            "voice_document": doc
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No voice document found for client: {client_id}")


@app.post("/voice/{client_id}/tune")
def tune_voice(client_id: str, req: UpdateVoiceRequest):
    """
    Creates a new version of the Voice Document with updated calibration.
    Use after reviewing performance data.
    """
    try:
        current_doc = load_voice_document(client_id, base_path=VOICES_PATH)
        versions = list_versions(client_id, base_path=VOICES_PATH)
        new_version = max(versions) + 1

        # Append tuning notes to the document
        tuning_section = f"\n\n## TUNING UPDATE — Version {new_version} ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        if req.calibration_notes:
            tuning_section += f"**Calibration notes:** {req.calibration_notes}\n\n"
        if req.additional_banned_words:
            tuning_section += f"**Additional banned words:** {', '.join(req.additional_banned_words)}\n\n"
        if req.performance_insights:
            tuning_section += f"**Performance insights:** {req.performance_insights}\n\n"

        updated_doc = current_doc + tuning_section
        saved_path = save_voice_document(updated_doc, client_id, new_version, VOICES_PATH)

        return {
            "client_id": client_id,
            "new_version": new_version,
            "saved_path": saved_path,
            "voice_document": updated_doc
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No voice document found for client: {client_id}")


# --- Performance tracking ---

class PerformanceLogRequest(BaseModel):
    post_id: str
    platform: str
    likes: int = 0
    comments: int = 0
    shares: int = 0
    impressions: int = 0
    clicks: int = 0


@app.post("/performance/{client_id}/log")
def log_performance_endpoint(client_id: str, req: PerformanceLogRequest):
    """Logs engagement data against a post."""
    try:
        from tracker.performance import log_performance
        result = log_performance(
            client_id, req.post_id, req.platform,
            req.likes, req.comments, req.shares,
            req.impressions, req.clicks,
            base_path=VOICES_PATH
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/{client_id}/report")
def get_performance_report(client_id: str, days: int = 7):
    """Returns performance report for the last N days."""
    try:
        from tracker.performance import generate_weekly_report, generate_voice_tuning_brief
        report = generate_weekly_report(client_id, base_path=VOICES_PATH, days_back=days)
        if report.get("posts_tracked", 0) >= 5:
            tuning_brief = generate_voice_tuning_brief(report, client)
            report["tuning_recommendations"] = tuning_brief
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Brief queue ---

@app.get("/queue/{client_id}")
def get_brief_queue(client_id: str):
    """Returns RSS and narrative brief queue for a client."""
    from inputs.rss_monitor import load_brief_queue

    rss_queue = load_brief_queue(client_id, base_path=VOICES_PATH)

    # Also load narrative queue if exists
    narrative_queue = []
    narrative_file = Path(VOICES_PATH) / client_id / "narrative_queue.json"
    if narrative_file.exists():
        with open(narrative_file) as f:
            narrative_queue = json.load(f)

    return {
        "rss_briefs": [i for i in rss_queue if i.get("status") == "pending"],
        "narrative_alerts": [i for i in narrative_queue if i.get("status") == "pending"],
        "total": len([i for i in rss_queue if i.get("status") == "pending"]) +
                 len([i for i in narrative_queue if i.get("status") == "pending"])
    }


@app.post("/queue/{client_id}/run-monitor")
def run_monitor_now(client_id: str, background_tasks: BackgroundTasks):
    """Triggers an immediate monitor run in the background."""
    def _run():
        from publishing.scheduler import run_rss_cycle, run_x_cycle, load_client_config
        config = load_client_config(client_id, VOICES_PATH)
        run_rss_cycle(client_id, config, VOICES_PATH)
        run_x_cycle(client_id, config, VOICES_PATH)

    background_tasks.add_task(_run)
    return {"status": "monitor started", "client_id": client_id}


# --- Schedule approved posts ---

@app.post("/schedule/{client_id}/{post_id}")
def schedule_post(client_id: str, post_id: str, platforms: str = "linkedin,twitter"):
    """Schedules a specific approved post to Buffer."""
    try:
        from publishing.buffer_publisher import schedule_approved_post
        platform_list = [p.strip() for p in platforms.split(",")]
        result = schedule_approved_post(post_id, client_id, platform_list, VOICES_PATH)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Clients list ---

@app.get("/clients")
def list_clients():
    """Returns list of all client IDs with voice documents."""
    voices_dir = Path(VOICES_PATH)
    if not voices_dir.exists():
        return {"clients": []}

    clients = []
    for client_dir in voices_dir.iterdir():
        if client_dir.is_dir():
            versions = list_versions(client_dir.name, base_path=VOICES_PATH)
            if versions:
                posts_dir = client_dir / POSTS_DIR
                post_count = len(list(posts_dir.glob("*.json"))) if posts_dir.exists() else 0
                clients.append({
                    "client_id": client_dir.name,
                    "versions": versions,
                    "latest_version": max(versions),
                    "post_count": post_count
                })

    return {"clients": clients}
