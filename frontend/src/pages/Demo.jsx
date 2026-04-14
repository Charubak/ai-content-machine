import { useState } from "react";
import { API_BASE } from "../App";

const TONES = [
  { id: "hybrid", label: "Hybrid", desc: "Technical + accessible, occasional crypto humour" },
  { id: "degen", label: "Degen", desc: "Sharp, irreverent, crypto-native" },
  { id: "institutional", label: "Institutional", desc: "Authoritative, clean, measured" },
  { id: "founder", label: "Founder", desc: "Direct, shows the work, no corporate polish" },
];

const S = {
  page: { maxWidth: 820, margin: "0 auto", padding: "3rem 1.5rem" },
  header: { marginBottom: "2.5rem", animation: "fadeUp 0.4s ease" },
  label: { fontSize: "0.62rem", color: "rgba(245,166,35,0.55)", letterSpacing: "0.12em", marginBottom: "0.5rem", display: "block" },
  textarea: {
    width: "100%", background: "rgba(200,192,176,0.03)",
    border: "1px solid rgba(200,192,176,0.12)", color: "#c8c0b0",
    padding: "0.85rem", fontSize: "0.8rem",
    fontFamily: "'IBM Plex Mono', monospace",
    resize: "vertical", outline: "none", lineHeight: 1.7,
    transition: "border-color 0.15s",
  },
  btn: (active) => ({
    background: active ? "rgba(245,166,35,0.12)" : "transparent",
    border: `1px solid ${active ? "rgba(245,166,35,0.5)" : "rgba(200,192,176,0.15)"}`,
    color: active ? "#f5a623" : "rgba(200,192,176,0.5)",
    padding: "0.45rem 0.9rem", fontSize: "0.68rem",
    letterSpacing: "0.08em", cursor: "pointer",
    fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.15s",
  }),
  runBtn: (disabled) => ({
    background: disabled ? "rgba(245,166,35,0.05)" : "rgba(245,166,35,0.12)",
    border: `1px solid ${disabled ? "rgba(245,166,35,0.2)" : "rgba(245,166,35,0.5)"}`,
    color: disabled ? "rgba(245,166,35,0.3)" : "#f5a623",
    padding: "0.65rem 1.8rem", fontSize: "0.72rem",
    letterSpacing: "0.12em", cursor: disabled ? "not-allowed" : "pointer",
    fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.15s",
  }),
  outputBox: {
    border: "1px solid rgba(245,166,35,0.15)",
    background: "rgba(200,192,176,0.02)",
    padding: "1.2rem", marginBottom: "1rem",
    animation: "fadeUp 0.3s ease",
  },
  tabBtn: (active) => ({
    background: "transparent",
    border: "none",
    borderBottom: active ? "2px solid #f5a623" : "2px solid transparent",
    color: active ? "#f5a623" : "rgba(200,192,176,0.4)",
    padding: "0.45rem 0.9rem", fontSize: "0.63rem",
    letterSpacing: "0.1em", cursor: "pointer",
    fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.15s",
    textTransform: "uppercase",
  }),
};

function ScoreBadge({ label, score }) {
  const color = score <= 3 ? "#5cb85c" : score <= 6 ? "#f0ad4e" : "#d9534f";
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontSize: "0.55rem", color: "rgba(200,192,176,0.35)", letterSpacing: "0.1em" }}>{label}</div>
      <div style={{ fontSize: "1.4rem", fontFamily: "'Playfair Display', serif", color, lineHeight: 1.1 }}>{score}</div>
    </div>
  );
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard?.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
      style={{ ...S.btn(false), fontSize: "0.6rem", marginTop: "0.8rem" }}
    >
      {copied ? "COPIED ✓" : "COPY"}
    </button>
  );
}

function LoadingDots() {
  return (
    <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: 5, height: 5, background: "#f5a623", borderRadius: "50%",
          animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  );
}

export default function Demo() {
  const [thought, setThought] = useState("");
  const [tone, setTone] = useState("hybrid");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("linkedin_long");

  const run = async () => {
    if (!thought.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_thought: thought, tone }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Generation failed");
      const data = await res.json();
      setResult(data);
      setActiveTab("linkedin_long");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const TABS = [
    { id: "linkedin_long", label: "LinkedIn Long" },
    { id: "linkedin_short", label: "LinkedIn Short" },
    { id: "x_thread", label: "X Thread" },
    { id: "x_single", label: "X Single" },
  ];

  const getContent = () => {
    if (!result) return "";
    if (activeTab === "x_thread") return result.x_thread?.join("\n\n") || "";
    return result[activeTab] || "";
  };

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={{ ...S.header, borderBottom: "1px solid rgba(245,166,35,0.12)", paddingBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.15em", marginBottom: "0.5rem" }}>
          ◆ LIVE DEMO
        </div>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: "2rem", color: "#e8dcc8", fontWeight: 700, lineHeight: 1.2, marginBottom: "0.75rem" }}>
          AI Content Machine
        </h1>
        <p style={{ color: "rgba(200,192,176,0.5)", fontSize: "0.78rem", lineHeight: 1.7, maxWidth: 560 }}>
          Paste a raw thought. Pick a voice. Get a LinkedIn post, short post, X thread, and single tweet — all passing a 25-pattern AI quality gate. No login required.
        </p>
      </div>

      {/* Tone selector */}
      <div style={{ marginBottom: "1.5rem" }}>
        <span style={S.label}>VOICE TONE</span>
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          {TONES.map(t => (
            <button key={t.id} onClick={() => setTone(t.id)} style={S.btn(tone === t.id)}>
              {t.label}
            </button>
          ))}
        </div>
        <div style={{ fontSize: "0.65rem", color: "rgba(200,192,176,0.35)", marginTop: "0.4rem" }}>
          {TONES.find(t => t.id === tone)?.desc}
        </div>
      </div>

      {/* Input */}
      <div style={{ marginBottom: "1.2rem" }}>
        <span style={S.label}>YOUR RAW THOUGHT</span>
        <textarea
          value={thought}
          onChange={e => setThought(e.target.value)}
          rows={5}
          placeholder="Type or paste a raw thought, opinion, or observation. The rougher the better — that's the point."
          style={S.textarea}
          onFocus={e => e.target.style.borderColor = "rgba(245,166,35,0.35)"}
          onBlur={e => e.target.style.borderColor = "rgba(200,192,176,0.12)"}
        />
      </div>

      {/* Run */}
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "2rem" }}>
        <button onClick={run} disabled={loading || !thought.trim()} style={S.runBtn(loading || !thought.trim())}>
          {loading ? "GENERATING..." : "GENERATE CONTENT ▶"}
        </button>
        {loading && <LoadingDots />}
      </div>

      {error && (
        <div style={{ border: "1px solid rgba(255,80,80,0.25)", background: "rgba(255,80,80,0.04)", padding: "0.8rem", marginBottom: "1rem" }}>
          <span style={{ color: "#ff6060", fontSize: "0.72rem" }}>ERROR: {error}</span>
        </div>
      )}

      {/* Output */}
      {result && (
        <div style={{ animation: "fadeUp 0.4s ease" }}>
          {/* Scores */}
          <div style={{
            border: "1px solid rgba(245,166,35,0.15)",
            background: "rgba(245,166,35,0.03)",
            padding: "1rem 1.2rem",
            marginBottom: "1rem",
            display: "flex",
            gap: "2rem",
            alignItems: "center",
          }}>
            <ScoreBadge label="BEFORE" score={result.score_before} />
            <span style={{ color: "rgba(245,166,35,0.3)", fontSize: "1.2rem" }}>→</span>
            <ScoreBadge label="AFTER" score={result.score_after} />
            <div style={{ marginLeft: "auto", fontSize: "0.65rem", color: "rgba(200,192,176,0.35)" }}>
              AI SLOP SCORE (1 = human, 10 = slop)
            </div>
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", borderBottom: "1px solid rgba(245,166,35,0.12)", marginBottom: "0" }}>
            {TABS.map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={S.tabBtn(activeTab === tab.id)}>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div style={{ ...S.outputBox, borderTop: "none" }}>
            <pre style={{
              fontSize: "0.78rem", lineHeight: 1.8, color: "#e8dcc8",
              whiteSpace: "pre-wrap", fontFamily: "'IBM Plex Mono', monospace",
              margin: 0,
            }}>
              {getContent()}
            </pre>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.75rem" }}>
              <CopyButton text={getContent()} />
              {activeTab === "x_single" && (
                <span style={{ fontSize: "0.6rem", color: "rgba(200,192,176,0.3)" }}>
                  {result.x_single?.length || 0} chars
                </span>
              )}
            </div>
          </div>

          {/* CTA */}
          <div style={{
            border: "1px solid rgba(245,166,35,0.12)",
            padding: "1.2rem",
            marginTop: "1.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <div>
              <div style={{ fontSize: "0.78rem", color: "#e8dcc8", marginBottom: "0.2rem" }}>
                Want this calibrated to your voice?
              </div>
              <div style={{ fontSize: "0.65rem", color: "rgba(200,192,176,0.4)" }}>
                30-minute onboarding. Your voice document. Consistent content every week.
              </div>
            </div>
            <button
              onClick={() => window.dispatchEvent(new CustomEvent("navigate", { detail: "hire" }))}
              style={{ ...S.btn(true), whiteSpace: "nowrap" }}
            >
              WORK WITH ME →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
