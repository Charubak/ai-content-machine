// HowItWorks.jsx
export function HowItWorks() {
  const S = {
    page: { maxWidth: 780, margin: "0 auto", padding: "3rem 1.5rem" },
    section: { marginBottom: "2.5rem" },
    h2: { fontFamily: "'Playfair Display', serif", fontSize: "1.15rem", color: "#e8dcc8", marginBottom: "0.75rem" },
    p: { fontSize: "0.78rem", color: "rgba(200,192,176,0.65)", lineHeight: 1.8 },
    step: {
      display: "flex", gap: "1.2rem", marginBottom: "1.2rem",
      borderLeft: "2px solid rgba(245,166,35,0.2)", paddingLeft: "1rem",
    },
    num: { fontSize: "0.6rem", color: "#f5a623", letterSpacing: "0.1em", marginBottom: "0.2rem" },
    code: {
      background: "rgba(245,166,35,0.07)", border: "1px solid rgba(245,166,35,0.15)",
      padding: "0.8rem 1rem", fontSize: "0.7rem", color: "#f5a623",
      fontFamily: "'IBM Plex Mono', monospace", display: "block", marginTop: "0.5rem",
    },
  };

  const steps = [
    {
      title: "Voice Onboarding (30-45 min)",
      desc: "Structured intake: brand identity, writing samples, best posts, voice rules. Output: a versioned Voice Document that becomes the system prompt for all generation. Can be tuned at any time."
    },
    {
      title: "Daily Brief Queue",
      desc: "RSS monitor polls 10+ feeds every 6 hours. AI scores each item for relevance to your content pillars. Top items become suggested briefs in your dashboard, ready to generate from."
    },
    {
      title: "Content Generation",
      desc: "One brief input → four platform variants: LinkedIn long-form, LinkedIn short, X thread, X single tweet. Each runs through a 25-pattern AI quality gate before returning. Failing outputs are automatically rewritten."
    },
    {
      title: "Narrative Fast-Path",
      desc: "Breaking news or viral content in your niche? Paste it, hit react. LinkedIn short + X single generated in under 30 seconds to hit the 2-4 hour window where timely content matters."
    },
    {
      title: "Review and Schedule",
      desc: "All content lands in the review dashboard as pending. You approve or reject. Approved posts publish via Buffer at scheduled times. Nothing goes live without human review."
    },
    {
      title: "Voice Tuning",
      desc: "Monthly: review which posts performed best. Feed that insight back into the Voice Document as a new version. The system compounds over time — month 3 output is materially better than month 1."
    },
  ];

  const stack = [
    ["Generation", "Claude Sonnet 4.6 (Anthropic API)"],
    ["Quality Gate", "25-pattern humanizer (blader/humanizer framework)"],
    ["Backend", "FastAPI (Python)"],
    ["Frontend", "React + Vite"],
    ["Orchestration", "n8n or Python cron"],
    ["Scheduling", "Buffer API"],
    ["Feed Monitoring", "feedparser + Anthropic relevance scoring"],
    ["Voice Storage", "Versioned markdown files"],
  ];

  return (
    <div style={S.page}>
      <div style={{ marginBottom: "2.5rem" }}>
        <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.15em", marginBottom: "0.5rem" }}>◆ ARCHITECTURE</div>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.7rem", color: "#e8dcc8", marginBottom: "0.7rem" }}>How It Works</h1>
        <p style={S.p}>
          A modular AI content system. Each component works independently and connects into a full pipeline.
          Open source on GitHub. Designed to be cloned, extended, and adapted.
        </p>
      </div>

      <div style={S.section}>
        <h2 style={S.h2}>The Pipeline</h2>
        {steps.map((step, i) => (
          <div key={i} style={S.step}>
            <div style={{ flex: 1 }}>
              <div style={S.num}>STEP {String(i + 1).padStart(2, "0")}</div>
              <div style={{ fontSize: "0.8rem", color: "#e8dcc8", marginBottom: "0.3rem" }}>{step.title}</div>
              <div style={S.p}>{step.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={S.section}>
        <h2 style={S.h2}>Tech Stack</h2>
        <div style={{ border: "1px solid rgba(200,192,176,0.08)" }}>
          {stack.map(([layer, detail], i) => (
            <div key={i} style={{
              display: "flex", gap: "1rem",
              padding: "0.65rem 1rem",
              borderBottom: i < stack.length - 1 ? "1px solid rgba(200,192,176,0.06)" : "none",
            }}>
              <div style={{ fontSize: "0.65rem", color: "rgba(245,166,35,0.6)", width: 110, flexShrink: 0 }}>{layer}</div>
              <div style={{ fontSize: "0.68rem", color: "rgba(200,192,176,0.55)" }}>{detail}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={S.section}>
        <h2 style={S.h2}>Run It Yourself</h2>
        <code style={S.code}>
          git clone https://github.com/Charubak/ai-content-machine{"\n"}
          cd ai-content-machine{"\n"}
          cp .env.example .env  # add your ANTHROPIC_API_KEY{"\n"}
          pip install -r backend/requirements.txt{"\n"}
          uvicorn backend.main:app --reload{"\n"}
          {"\n"}
          # Frontend{"\n"}
          cd frontend && npm install && npm run dev
        </code>
        <div style={{ marginTop: "1rem" }}>
          <a href="https://github.com/Charubak/ai-content-machine" target="_blank" rel="noreferrer"
            style={{ fontSize: "0.68rem", color: "#f5a623", textDecoration: "none" }}>
            → github.com/Charubak/ai-content-machine
          </a>
        </div>
      </div>
    </div>
  );
}

export default HowItWorks;
