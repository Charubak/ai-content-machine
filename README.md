# AI Content Machine

> AI-powered content engine for Web3 and AI-first brands. Voice calibration, 25-pattern quality gate, FastAPI + React.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-orange?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Built by [Charubak Chakrabarti](https://linkedin.com/in/charubak) — senior Web3/DeFi growth marketer and AI tools builder.

---

## The Problem

Most founders and DeFi protocols have strong opinions and no time to write. The ones who do write sound like every other Web3 account — vague, hype-heavy, and forgettable. Generic AI tools make it worse: they strip out voice and add em dashes.

This system solves the actual problem: consistent, high-quality content that sounds like a specific human, not a language model.

---

## How It Works

```
Writing samples + intake
         ↓
  Voice Document (your system prompt)
         ↓
  Brief → Generate → Quality Gate → Review → Publish
                          ↓
               Fails 25-pattern check?
                    Auto-rewrite
```

1. **Voice Onboarding** — A 30-45 min session produces a versioned Voice Document from your writing samples, best posts, and structured intake. Every post sounds like you — not generic AI.

2. **Content Generation** — One brief → LinkedIn long-form, LinkedIn short, X thread, and X single tweet. All run through a 25-pattern AI quality gate before returning.

3. **Narrative Fast-Path** — Paste breaking news, get a reaction post in 30 seconds. Hit the 2-4 hour window where timely content matters.

4. **Brief Queue** — RSS monitor polls curated feeds, scores relevance to your content pillars, and surfaces the best brief opportunities every morning.

5. **Review Dashboard** — React frontend. Generate, review, approve, reject, mark published. Nothing goes live without human review.

6. **Voice Tuning** — Monthly updates based on performance data. The system compounds over time.

---

## Live Demo

**[web3growthlab.com/content-machine](https://web3growthlab.com/content-machine)** — no login required.

Paste a raw thought, pick a tone, and get 4 platform variants with slop scores in ~10 seconds.

| | URL |
|---|---|
| Frontend | https://web3growthlab.com/content-machine |
| Backend API | https://ai-content-machine-api.fly.dev |
| API Docs | https://ai-content-machine-api.fly.dev/docs |

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Node.js 18+
- [Anthropic API key](https://console.anthropic.com)

### 1. Clone & configure

```bash
git clone https://github.com/Charubak/ai-content-machine.git
cd ai-content-machine

cp .env.example .env
# Open .env and set: ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- API running at: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
# UI at: http://localhost:3000
```

### 4. Test the pipeline

1. Go to http://localhost:3000 → **Demo** tab
2. Paste a raw thought (e.g. *"Founders writing publicly is the most underused marketing tool in Web3"*)
3. Select **Hybrid** tone
4. Hit **Generate Content**
5. You'll get 4 content variants with slop scores

> **Already deployed?** The live version is at [web3growthlab.com/content-machine](https://web3growthlab.com/content-machine) — backend on Fly.io at `ai-content-machine-api.fly.dev`.

---

## Docker Deploy

The fastest way to run the full stack in production:

```bash
cp .env.example .env
# Add all API keys to .env

docker-compose up -d

# Verify all containers are running
docker-compose ps
docker-compose logs backend
```

This starts three containers:
- `backend` — FastAPI on port 8000
- `frontend` — Nginx serving the React app on port 3000
- `scheduler` — Background process polling RSS + X feeds every 2-6 hours

---

## Project Structure

```
ai-content-machine/
├── backend/
│   ├── main.py                 # FastAPI app, 21 endpoints
│   ├── agents/
│   │   ├── content_agent.py    # Core generation pipeline, 4 platform variants
│   │   ├── humanizer.py        # 25-pattern AI writing detector + rewriter
│   │   └── voice_builder.py    # Voice Document generator from writing samples
│   ├── inputs/
│   │   ├── rss_monitor.py      # RSS feed aggregator + AI relevance scoring
│   │   └── x_monitor.py        # X keyword monitor for narrative hijacking
│   ├── publishing/
│   │   ├── buffer_publisher.py # Buffer API scheduling integration
│   │   └── scheduler.py        # Background process, runs monitors on interval
│   ├── tracker/
│   │   └── performance.py      # Engagement tracking + weekly report generation
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── App.jsx             # Navigation shell
│       └── pages/
│           ├── Demo.jsx        # Public live demo (no login required)
│           ├── Onboarding.jsx  # 4-stage voice intake wizard
│           ├── Dashboard.jsx   # Generate, review, approve queue
│           ├── HowItWorks.jsx  # Architecture + tech stack
│           └── WorkWithMe.jsx  # Service tiers + contact
│
├── voices/
│   └── charubak/
│       └── voice_v1.md         # Example Voice Document (146 lines)
│
├── docker-compose.yml          # 3-container production deploy
├── onboard_cli.py              # Terminal voice onboarding for new clients
└── .env.example
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/demo` | Public demo — generate content, no client ID required |
| POST | `/onboard` | Create a new client and build their Voice Document |
| POST | `/generate` | Generate content from a brief (requires client ID) |
| POST | `/react` | Fast-path reaction post from a news item |
| POST | `/humanize` | Run the 25-pattern quality gate on any text |
| GET | `/voice/{client_id}` | Fetch the current Voice Document |
| POST | `/voice/{client_id}/tune` | Add calibration notes and create new voice version |
| GET | `/posts/{client_id}` | Post history with statuses |
| PATCH | `/posts/{client_id}/{post_id}` | Update post status (approved/rejected/published) |
| GET | `/queue/{client_id}` | Get brief suggestions from RSS monitor |
| GET | `/clients` | List all configured clients |

Full interactive docs:
- **Production:** https://ai-content-machine-api.fly.dev/docs
- **Local:** http://localhost:8000/docs

---

## Voice Documents

Each client gets a versioned markdown Voice Document stored at `voices/{client_id}/voice_v{N}.md`. It contains:

- **Identity** — one-liner positioning and target audience
- **Tone profile** — specific descriptors, not just "professional" or "casual"
- **Content pillars** — 5-7 core topics with angles
- **Observed voice patterns** — extracted from actual writing samples
- **Banned words** — full list (delve, tapestry, vibrant, pivotal, synergy, leverage, cutting-edge, and more)
- **Required phrases** — terminology that signals authentic expertise
- **Format rules** — hook structure, sentence length variance, platform-specific conventions
- **Failure conditions** — explicit criteria for when a post is rejected

The Voice Document is the system prompt for every generation call. Its quality directly determines output quality.

To onboard a new client:

```bash
# Via terminal
python onboard_cli.py --client-id yourname

# Or via the web UI
# Go to https://web3growthlab.com/content-machine → Voice Setup tab
```

---

## The 25 AI Writing Patterns

The humanizer quality gate detects and auto-rewrites:

| # | Pattern | Example |
|---|---------|---------|
| 1 | Undue significance | *"a pivotal moment in history"* |
| 2 | Notability overclaiming | *"one of the most important..."* |
| 3 | Superficial -ing endings | *"showcasing", "highlighting"* |
| 4 | Promotional language | *"game-changing", "revolutionary"* |
| 5 | Vague attributions | *"experts say", "many believe"* |
| 6 | Formulaic challenge sections | *"Despite these challenges..."* |
| 7 | AI vocabulary | *delve, tapestry, vibrant, nuanced* |
| 8 | Copula avoidance | *"serves as", "stands as"* |
| 9 | Negative parallelisms | *"not just X, but Y"* |
| 10 | Filler transitions | *"In conclusion", "It's worth noting"* |
| 11 | Em dash overuse | *— inserted everywhere —* |
| 12 | Colon list overuse | *"three things: X, Y, Z"* |
| 13 | Passive voice overuse | *"was created by", "is being used"* |
| 14 | Rule of three | *"fast, reliable, and scalable"* |
| 15 | Hollow affirmatives | *"Certainly!", "Absolutely!"* |
| 16 | Sycophantic openers | *"Great question!"* |
| 17 | Hyphenated overclaiming | *"ever-evolving", "thought-provoking"* |
| 18 | Directness failures | *burying the point in qualifiers* |
| 19 | Formulaic endings | *"only time will tell"* |
| 20 | Journey overuse | *"on this journey", "our journey"* |
| 21 | Unnecessary capitalisation | *"the Industry", "our Vision"* |
| 22 | Serial list padding | *adding items just to hit a number* |
| 23 | Rhetorical question openers | *"Have you ever wondered..."* |
| 24 | Timestamp hedging | *"as of my last update"* |
| 25 | Soulless writing | technically clean but no distinct voice |

Based on [blader/humanizer](https://github.com/blader/humanizer) and Wikipedia's documented signs of AI writing.

---

## Tech Stack

| Layer | Tech | Notes |
|-------|------|-------|
| LLM | Claude Sonnet 4.6 (Anthropic) | Primary generation + quality rewrite |
| Quality gate | 25-pattern humanizer | Based on blader/humanizer + Wikipedia |
| Backend | FastAPI (Python 3.11) | 21 endpoints |
| Frontend | React 18 + Vite | 5 pages, no external UI library |
| Orchestration | Python scheduler | Polls feeds every 2-6 hours |
| Scheduling | Buffer API | LinkedIn + X publishing |
| Feed monitoring | feedparser + httpx | 10+ RSS sources |
| X monitoring | X API v2 (Bearer Token) | Narrative hijacking |
| Voice storage | Versioned markdown files | One file per client per version |
| Deploy | Docker Compose | 3 containers |

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional — enables Buffer scheduling
BUFFER_ACCESS_TOKEN=...

# Optional — enables X feed monitoring
X_BEARER_TOKEN=...

# Optional — enables LinkedIn performance tracking
LINKEDIN_ACCESS_TOKEN=...
```

---

## Done-For-You Service

Don't want to run it yourself? I operate this system for Web3 and AI-first brands.

**Starter — $1,500/mo**
12 posts/month across LinkedIn and X. Covers 1 client voice.

**Growth — $3,000/mo**
25 posts/month + weekly long-form article. Narrative fast-path included.

**Scale — $5,000/mo**
40 posts/month + community content + performance reports.

All tiers include: 30-min voice onboarding, Voice Document, monthly voice tuning, human review before every post goes live.

**First step:** [web3growthlabs.com](https://web3growthlabs.com) · [charubak.chakrabarti@gmail.com](mailto:charubak.chakrabarti@gmail.com)

---

## License

MIT. Fork it, adapt it, build on it.

If you use it in production, a GitHub star is appreciated.
