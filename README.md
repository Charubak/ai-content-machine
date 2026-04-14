# AI Content Machine

A modular AI content system for Web3 and AI-first brands. Voice calibration, automated content generation, 25-pattern quality gate, narrative hijacking, review dashboard.

Built by [Charubak Chakrabarti](https://linkedin.com/in/charubak) — senior Web3/DeFi growth marketer and AI tools builder.

---

## What It Does

1. **Voice Onboarding** — 30-45 min session produces a versioned Voice Document from writing samples, best posts, and structured intake. Every post sounds like this specific human, not generic AI.

2. **Content Generation** — One brief → LinkedIn long-form, LinkedIn short, X thread, X single tweet. All run through a 25-pattern AI quality gate before returning.

3. **Narrative Fast-Path** — Paste breaking news, get a reaction post in 30 seconds. Hit the 2-4 hour window where timely content matters.

4. **Brief Queue** — RSS monitor polls curated feeds, scores relevance to your content pillars, surfaces the best brief opportunities every morning.

5. **Review Dashboard** — React frontend. Review, approve, reject, mark published. Nothing goes live without human review.

6. **Voice Tuning** — Monthly updates based on performance data. The system compounds over time.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend

```bash
cd backend
cp ../.env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install

# Set API URL (optional, defaults to localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env

npm run dev
# Runs at http://localhost:3000
```

---

## Project Structure

```
ai-content-machine/
├── backend/
│   ├── main.py                 # FastAPI app, all endpoints
│   ├── agents/
│   │   ├── content_agent.py    # Core generation + quality gate pipeline
│   │   ├── humanizer.py        # 25-pattern AI writing detector + rewriter
│   │   └── voice_builder.py    # Voice Document generator from samples
│   ├── inputs/
│   │   └── rss_monitor.py      # Feed aggregator + brief queue
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── App.jsx             # Navigation shell
│       └── pages/
│           ├── Demo.jsx        # Public live demo (no login)
│           ├── Onboarding.jsx  # 4-stage voice intake wizard
│           ├── Dashboard.jsx   # Generate, review, approve
│           ├── HowItWorks.jsx  # Architecture + GitHub
│           └── WorkWithMe.jsx  # Service offer + contact
│
├── voices/                     # Client Voice Documents (git-ignored in production)
│   └── [client_id]/
│       ├── voice_v1.md         # Versioned voice documents
│       ├── brief_queue.json    # RSS-generated brief suggestions
│       └── posts/              # Generated post history
│
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/demo` | Public demo, no client ID needed |
| POST | `/onboard` | Create client + Voice Document |
| POST | `/generate` | Generate content from brief |
| POST | `/react` | Fast-path narrative reaction |
| POST | `/humanize` | Quality gate check on any text |
| GET | `/posts/{client_id}` | Post history |
| PATCH | `/posts/{client_id}/{post_id}` | Update post status |
| GET | `/voice/{client_id}` | Get Voice Document |
| POST | `/voice/{client_id}/tune` | Create new voice version |
| GET | `/clients` | List all clients |

Full interactive docs: `http://localhost:8000/docs`

---

## Running the RSS Monitor

```bash
# Run once manually for a client
python backend/inputs/rss_monitor.py charubak

# Or schedule with cron (every 6 hours)
0 */6 * * * cd /path/to/ai-content-machine && python backend/inputs/rss_monitor.py charubak
```

---

## Voice Document Format

Each client gets a markdown Voice Document stored in `voices/{client_id}/voice_v{N}.md`. It contains:

- Identity and one-liner
- Tone profile with specific descriptors
- Content pillars (5-7 topics)
- Observed voice patterns (extracted from writing samples)
- Best performing post references
- Banned words and phrases
- Required phrases and terminology
- Always-true content rules
- Platform format rules
- Failure conditions

The Voice Document is the system prompt for every generation call. Its quality directly determines output quality.

---

## The 25 AI Writing Patterns

The humanizer quality gate checks for:

1. Undue emphasis on significance/legacy
2. Notability overclaiming
3. Superficial -ing endings
4. Promotional language
5. Vague attributions
6. Formulaic challenges sections
7. AI vocabulary words (delve, tapestry, vibrant, pivotal, etc.)
8. Copula avoidance (serves as, stands as)
9. Negative parallelisms
10. Filler transition phrases
11. Em dash overuse
12. Colon list overuse
13. Passive voice overuse
14. Rule of three overuse
15. Hollow affirmatives (Certainly!, Absolutely!)
16. Sycophantic openers
17. Hyphenated word pairs (ever-evolving, game-changing)
18. Directness failures
19. Formulaic endings
20. Overuse of "journey"
21. Unnecessary capitalisation
22. Serial list padding
23. Rhetorical question openers
24. Timestamp hedging
25. Soulless writing (technically clean but no voice)

Based on [blader/humanizer](https://github.com/blader/humanizer) and Wikipedia's "Signs of AI writing".

---

## Done For You Service

Don't want to run it yourself? I operate this system for Web3 and AI-first brands.

**Starter** — $1,500/mo — 12 posts/month  
**Growth** — $3,000/mo — 25 posts/month + weekly long-form  
**Scale** — $5,000/mo — 40 posts/month + community content  

[web3growthlabs.com](https://web3growthlabs.com) · [charubak.chakrabarti@gmail.com](mailto:charubak.chakrabarti@gmail.com)

---

## License

MIT. Build on it, fork it, adapt it.

If you use it in production, a mention or star on the repo is appreciated.
