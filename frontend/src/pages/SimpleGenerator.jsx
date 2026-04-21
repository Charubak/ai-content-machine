import { useState } from "react";
import { API_BASE } from "../App";

// ─── Shared Styles ─────────────────────────────────────────────────────────

const S = {
  page: { maxWidth: 780, margin: "0 auto", padding: "3rem 1.5rem" },

  label: {
    fontSize: "0.6rem",
    color: "rgba(245,166,35,0.55)",
    letterSpacing: "0.12em",
    marginBottom: "0.5rem",
    display: "block",
    textTransform: "uppercase",
  },

  textarea: {
    width: "100%",
    background: "rgba(200,192,176,0.03)",
    border: "1px solid rgba(200,192,176,0.12)",
    color: "#c8c0b0",
    padding: "0.85rem",
    fontSize: "0.82rem",
    fontFamily: "'IBM Plex Mono', monospace",
    resize: "vertical",
    outline: "none",
    lineHeight: 1.7,
    transition: "border-color 0.15s",
  },

  modeBtn: (active) => ({
    background: active ? "rgba(245,166,35,0.1)" : "transparent",
    border: `1px solid ${active ? "rgba(245,166,35,0.4)" : "rgba(200,192,176,0.12)"}`,
    color: active ? "#f5a623" : "rgba(200,192,176,0.4)",
    padding: "0.5rem 1.2rem",
    fontSize: "0.65rem",
    letterSpacing: "0.1em",
    cursor: "pointer",
    fontFamily: "'IBM Plex Mono', monospace",
    transition: "all 0.15s",
    textTransform: "uppercase",
  }),

  runBtn: (disabled) => ({
    background: disabled ? "rgba(245,166,35,0.04)" : "rgba(245,166,35,0.12)",
    border: `1px solid ${disabled ? "rgba(245,166,35,0.15)" : "rgba(245,166,35,0.5)"}`,
    color: disabled ? "rgba(245,166,35,0.25)" : "#f5a623",
    padding: "0.7rem 2rem",
    fontSize: "0.72rem",
    letterSpacing: "0.12em",
    cursor: disabled ? "not-allowed" : "pointer",
    fontFamily: "'IBM Plex Mono', monospace",
    transition: "all 0.15s",
  }),

  card: {
    border: "1px solid rgba(245,166,35,0.12)",
    background: "rgba(200,192,176,0.02)",
    padding: "1.5rem",
    marginBottom: "1.2rem",
    animation: "fadeUp 0.35s ease",
  },

  cardTitle: {
    fontSize: "0.58rem",
    color: "rgba(245,166,35,0.45)",
    letterSpacing: "0.15em",
    textTransform: "uppercase",
    marginBottom: "1rem",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },

  text: {
    fontSize: "0.82rem",
    lineHeight: 1.75,
    color: "#c8c0b0",
    whiteSpace: "pre-wrap",
  },

  tab: (active) => ({
    background: "transparent",
    border: "none",
    borderBottom: active ? "2px solid #f5a623" : "2px solid transparent",
    color: active ? "#f5a623" : "rgba(200,192,176,0.4)",
    padding: "0.45rem 0.9rem",
    fontSize: "0.62rem",
    letterSpacing: "0.1em",
    cursor: "pointer",
    fontFamily: "'IBM Plex Mono', monospace",
    transition: "all 0.15s",
    textTransform: "uppercase",
  }),

  error: {
    border: "1px solid rgba(217,83,79,0.3)",
    background: "rgba(217,83,79,0.05)",
    color: "rgba(217,83,79,0.8)",
    padding: "0.8rem",
    fontSize: "0.75rem",
    marginTop: "1rem",
  },

  hint: {
    fontSize: "0.62rem",
    color: "rgba(200,192,176,0.28)",
    marginTop: "0.4rem",
    lineHeight: 1.5,
  },
};

// ─── Shared Components ─────────────────────────────────────────────────────

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard?.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      style={{
        background: "transparent",
        border: "1px solid rgba(200,192,176,0.15)",
        color: copied ? "#5cb85c" : "rgba(200,192,176,0.4)",
        padding: "0.25rem 0.6rem",
        fontSize: "0.58rem",
        letterSpacing: "0.08em",
        cursor: "pointer",
        fontFamily: "'IBM Plex Mono', monospace",
        flexShrink: 0,
      }}
    >
      {copied ? "COPIED ✓" : "COPY"}
    </button>
  );
}

function LoadingDots() {
  return (
    <span style={{ display: "inline-flex", gap: "3px", alignItems: "center" }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: 4, height: 4,
            background: "#f5a623",
            borderRadius: "50%",
            animation: `pulse 1s ease ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </span>
  );
}

function ResetLink({ onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: "transparent", border: "none",
        color: "rgba(200,192,176,0.25)",
        fontSize: "0.62rem", letterSpacing: "0.08em",
        cursor: "pointer", fontFamily: "'IBM Plex Mono', monospace",
        marginTop: "1.5rem", padding: 0, textDecoration: "underline",
      }}
    >
      ← Start over
    </button>
  );
}

function ScoreBar({ before, after }) {
  if (before == null && after == null) return null;
  return (
    <div style={{
      display: "flex", gap: "2rem",
      padding: "0.8rem 0",
      borderTop: "1px solid rgba(200,192,176,0.06)",
      marginTop: "0.5rem",
    }}>
      {[{ label: "RAW SCORE", val: before }, { label: "AFTER GATE", val: after }].map(({ label, val }) => {
        if (val == null) return null;
        const color = val <= 3 ? "#5cb85c" : val <= 6 ? "#f0ad4e" : "#d9534f";
        return (
          <div key={label} style={{ textAlign: "center" }}>
            <div style={{ fontSize: "0.52rem", color: "rgba(200,192,176,0.3)", letterSpacing: "0.1em" }}>{label}</div>
            <div style={{ fontSize: "1.4rem", fontFamily: "'Playfair Display', serif", color, lineHeight: 1.1 }}>{val}</div>
          </div>
        );
      })}
      <div style={{ fontSize: "0.7rem", color: "rgba(200,192,176,0.3)", alignSelf: "center", paddingLeft: "0.5rem" }}>
        /10 slop score — lower is better
      </div>
    </div>
  );
}


// ─── Quick Generate ─────────────────────────────────────────────────────────

function QuickGenerate() {
  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [xTab, setXTab] = useState("thread");

  const canGenerate = idea.trim().length > 10 && !loading;

  async function generate() {
    if (!canGenerate) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API_BASE}/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_thought: idea.trim(), tone: "founder" }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Error ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      setError(e.message || "Generation failed.");
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <div>
        <div style={{ fontSize: "0.58rem", color: "rgba(245,166,35,0.3)", letterSpacing: "0.15em", marginBottom: "1.5rem" }}>
          OUTPUT — READY TO PUBLISH
        </div>

        <div style={S.card}>
          <div style={S.cardTitle}><span>LinkedIn — Long-form</span><CopyBtn text={result.linkedin_long} /></div>
          <div style={S.text}>{result.linkedin_long}</div>
        </div>

        <div style={S.card}>
          <div style={S.cardTitle}><span>LinkedIn — Short</span><CopyBtn text={result.linkedin_short} /></div>
          <div style={S.text}>{result.linkedin_short}</div>
        </div>

        <div style={S.card}>
          <div style={S.cardTitle}>
            <span>X / Twitter</span>
            <CopyBtn text={xTab === "thread" ? result.x_thread.join("\n\n") : result.x_single} />
          </div>
          <div style={{ display: "flex", gap: "0.1rem", borderBottom: "1px solid rgba(200,192,176,0.08)", marginBottom: "1.2rem" }}>
            <button style={S.tab(xTab === "thread")} onClick={() => setXTab("thread")}>Thread</button>
            <button style={S.tab(xTab === "single")} onClick={() => setXTab("single")}>Single tweet</button>
          </div>
          {xTab === "thread" && result.x_thread.map((t, i) => (
            <div key={i} style={{ borderLeft: "2px solid rgba(245,166,35,0.2)", paddingLeft: "0.9rem", marginBottom: "0.85rem", fontSize: "0.8rem", lineHeight: 1.65, color: "#c8c0b0" }}>
              <span style={{ fontSize: "0.55rem", color: "rgba(245,166,35,0.3)", letterSpacing: "0.1em", display: "block", marginBottom: "0.25rem" }}>
                {i + 1} / {result.x_thread.length}
              </span>
              {t}
            </div>
          ))}
          {xTab === "single" && <div style={{ ...S.text, color: "#e8dcc8" }}>{result.x_single}</div>}
        </div>

        <ScoreBar before={result.score_before} after={result.score_after} />
        <ResetLink onClick={() => { setResult(null); setIdea(""); }} />
      </div>
    );
  }

  return (
    <div>
      <label style={S.label}>Your idea</label>
      <textarea
        value={idea}
        onChange={(e) => setIdea(e.target.value)}
        placeholder="e.g. Most Web3 projects fail not because the tech is wrong but because they ship the product before they've built any trust with the community that needs to believe in it."
        rows={5}
        style={S.textarea}
        onFocus={(e) => (e.target.style.borderColor = "rgba(245,166,35,0.35)")}
        onBlur={(e) => (e.target.style.borderColor = "rgba(200,192,176,0.12)")}
        onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") generate(); }}
      />
      <div style={S.hint}>⌘ + Enter to generate</div>

      {error && <div style={{ ...S.error, marginBottom: "1rem" }}>{error}</div>}

      <div style={{ marginTop: "1.2rem" }}>
        <button onClick={generate} disabled={!canGenerate} style={S.runBtn(!canGenerate)}>
          {loading ? <><LoadingDots />&nbsp;&nbsp;GENERATING</> : "GENERATE CONTENT"}
        </button>
      </div>
    </div>
  );
}


// ─── Research Mode ──────────────────────────────────────────────────────────

function ResearchMode() {
  const [query, setQuery] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [expandedIdx, setExpandedIdx] = useState(0);

  const canSearch = query.trim().length > 5 && !loading;

  async function research() {
    if (!canSearch) return;
    setLoading(true); setError(""); setResults(null);
    try {
      const res = await fetch(`${API_BASE}/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          research_input: query.trim(),
          project_context: context.trim(),
        }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Error ${res.status}`);
      const data = await res.json();
      setResults(data);
      setExpandedIdx(0);
    } catch (e) {
      setError(e.message || "Research failed.");
    } finally {
      setLoading(false);
    }
  }

  if (results) {
    const { angles, search_powered } = results;
    return (
      <div>
        {/* Header strip */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: "1.5rem",
        }}>
          <div style={{ fontSize: "0.58rem", color: "rgba(245,166,35,0.3)", letterSpacing: "0.15em" }}>
            {angles.length} ANGLE{angles.length !== 1 ? "S" : ""} FOUND
          </div>
          <div style={{
            fontSize: "0.56rem",
            color: search_powered ? "rgba(92,184,92,0.6)" : "rgba(200,192,176,0.3)",
            letterSpacing: "0.08em",
            border: `1px solid ${search_powered ? "rgba(92,184,92,0.2)" : "rgba(200,192,176,0.1)"}`,
            padding: "0.2rem 0.6rem",
          }}>
            {search_powered ? "● LIVE SEARCH" : "○ CLAUDE KNOWLEDGE"}
          </div>
        </div>

        {/* Angle cards */}
        {angles.map((angle, idx) => (
          <AngleCard
            key={idx}
            angle={angle}
            index={idx}
            isExpanded={expandedIdx === idx}
            onToggle={() => setExpandedIdx(expandedIdx === idx ? -1 : idx)}
          />
        ))}

        <ResetLink onClick={() => { setResults(null); setQuery(""); setContext(""); }} />
      </div>
    );
  }

  return (
    <div>
      {/* Query input */}
      <div style={{ marginBottom: "1.2rem" }}>
        <label style={S.label}>What to research</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            "Specific: \"Kelp DAO exploit — what happened and what it means for restaking\"\n\n" +
            "Broad: \"Find the most relevant narratives in DeFi security right now\"\n\n" +
            "Project-driven: \"What's happening in the cross-chain bridge space that I should react to\""
          }
          rows={5}
          style={S.textarea}
          onFocus={(e) => (e.target.style.borderColor = "rgba(245,166,35,0.35)")}
          onBlur={(e) => (e.target.style.borderColor = "rgba(200,192,176,0.12)")}
          onKeyDown={(e) => { if ((e.metaKey || e.ctrlKey) && e.key === "Enter") research(); }}
        />
      </div>

      {/* Project context (optional) */}
      <div style={{ marginBottom: "1.5rem" }}>
        <label style={S.label}>Your project context <span style={{ color: "rgba(200,192,176,0.25)", fontWeight: 400 }}>(optional)</span></label>
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="e.g. We're building a non-custodial stablecoin on Arbitrum. Our angle is that yield shouldn't require trust in a centralised issuer."
          rows={3}
          style={S.textarea}
          onFocus={(e) => (e.target.style.borderColor = "rgba(245,166,35,0.35)")}
          onBlur={(e) => (e.target.style.borderColor = "rgba(200,192,176,0.12)")}
        />
        <div style={S.hint}>
          Adding context helps filter for angles that are actually relevant to your narrative.
        </div>
      </div>

      {error && <div style={{ ...S.error, marginBottom: "1rem" }}>{error}</div>}

      <button onClick={research} disabled={!canSearch} style={S.runBtn(!canSearch)}>
        {loading ? <><LoadingDots />&nbsp;&nbsp;RESEARCHING</> : "RESEARCH & GENERATE"}
      </button>

      {loading && (
        <div style={{ marginTop: "1rem", fontSize: "0.68rem", color: "rgba(200,192,176,0.3)", lineHeight: 1.8 }}>
          Searching for narratives → extracting angles → generating content
        </div>
      )}
    </div>
  );
}


// ─── Angle Card ─────────────────────────────────────────────────────────────

function AngleCard({ angle, index, isExpanded, onToggle }) {
  const [xTab, setXTab] = useState("single");

  return (
    <div style={{
      border: `1px solid ${isExpanded ? "rgba(245,166,35,0.25)" : "rgba(245,166,35,0.1)"}`,
      background: "rgba(200,192,176,0.02)",
      marginBottom: "1rem",
      animation: "fadeUp 0.35s ease",
      transition: "border-color 0.15s",
    }}>
      {/* Header — always visible, clickable */}
      <div
        onClick={onToggle}
        style={{
          padding: "1rem 1.5rem",
          cursor: "pointer",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "1rem",
        }}
      >
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: "0.55rem",
            color: "rgba(245,166,35,0.35)",
            letterSpacing: "0.12em",
            marginBottom: "0.4rem",
          }}>
            ANGLE {index + 1}
          </div>
          <div style={{
            fontSize: "0.88rem",
            color: "#e8dcc8",
            lineHeight: 1.5,
            fontFamily: "'Playfair Display', serif",
          }}>
            {angle.headline}
          </div>
          {angle.source_title && (
            <div style={{
              fontSize: "0.6rem",
              color: "rgba(200,192,176,0.3)",
              marginTop: "0.4rem",
              display: "flex", alignItems: "center", gap: "0.4rem",
            }}>
              <span>↳</span>
              {angle.source_url
                ? <a href={angle.source_url} target="_blank" rel="noopener noreferrer"
                    style={{ color: "rgba(245,166,35,0.4)", textDecoration: "none" }}
                    onClick={(e) => e.stopPropagation()}>
                    {angle.source_title}
                  </a>
                : <span>{angle.source_title}</span>
              }
            </div>
          )}
        </div>
        <span style={{
          fontSize: "0.65rem",
          color: "rgba(245,166,35,0.4)",
          flexShrink: 0,
          marginTop: "0.2rem",
        }}>
          {isExpanded ? "▲" : "▼"}
        </span>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div style={{ padding: "0 1.5rem 1.5rem" }}>
          {/* Key facts */}
          {angle.key_facts?.length > 0 && (
            <div style={{ marginBottom: "1.2rem" }}>
              <div style={{ fontSize: "0.55rem", color: "rgba(245,166,35,0.35)", letterSpacing: "0.12em", marginBottom: "0.5rem" }}>
                KEY FACTS
              </div>
              {angle.key_facts.map((fact, i) => (
                <div key={i} style={{
                  fontSize: "0.75rem", color: "rgba(200,192,176,0.6)",
                  paddingLeft: "0.8rem", marginBottom: "0.25rem",
                  borderLeft: "1px solid rgba(245,166,35,0.15)",
                }}>
                  {fact}
                </div>
              ))}
            </div>
          )}

          {/* Relevance */}
          {angle.relevance && (
            <div style={{ marginBottom: "1.2rem" }}>
              <div style={{ fontSize: "0.55rem", color: "rgba(245,166,35,0.35)", letterSpacing: "0.12em", marginBottom: "0.5rem" }}>
                WHY THIS MATTERS
              </div>
              <div style={{ fontSize: "0.76rem", color: "rgba(200,192,176,0.55)", lineHeight: 1.6 }}>
                {angle.relevance}
              </div>
            </div>
          )}

          <div style={{ borderTop: "1px solid rgba(200,192,176,0.06)", paddingTop: "1.2rem" }}>

            {/* LinkedIn short */}
            {angle.linkedin_short && (
              <div style={{ marginBottom: "1.2rem" }}>
                <div style={{
                  fontSize: "0.55rem", color: "rgba(245,166,35,0.35)",
                  letterSpacing: "0.12em", marginBottom: "0.7rem",
                  display: "flex", justifyContent: "space-between",
                }}>
                  <span>LINKEDIN POST</span>
                  <CopyBtn text={angle.linkedin_short} />
                </div>
                <div style={{ fontSize: "0.82rem", lineHeight: 1.75, color: "#c8c0b0", whiteSpace: "pre-wrap" }}>
                  {angle.linkedin_short}
                </div>
              </div>
            )}

            {/* X output */}
            {angle.x_single && (
              <div>
                <div style={{
                  fontSize: "0.55rem", color: "rgba(245,166,35,0.35)",
                  letterSpacing: "0.12em", marginBottom: "0.7rem",
                  display: "flex", justifyContent: "space-between",
                }}>
                  <span>X / TWEET</span>
                  <CopyBtn text={angle.x_single} />
                </div>
                <div style={{
                  fontSize: "0.82rem", lineHeight: 1.65,
                  color: "#e8dcc8", whiteSpace: "pre-wrap",
                  borderLeft: "2px solid rgba(245,166,35,0.15)",
                  paddingLeft: "0.9rem",
                }}>
                  {angle.x_single}
                </div>
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
}


// ─── Main Page ──────────────────────────────────────────────────────────────

export default function SimpleGenerator() {
  const [mode, setMode] = useState("quick"); // "quick" | "research"

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={{ marginBottom: "2rem", animation: "fadeUp 0.4s ease" }}>
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: "1.8rem",
          color: "#e8dcc8",
          fontWeight: 600,
          marginBottom: "0.5rem",
        }}>
          {mode === "quick" ? "Idea to post." : "Research to post."}
        </h1>
        <p style={{ fontSize: "0.76rem", color: "rgba(200,192,176,0.4)", lineHeight: 1.6 }}>
          {mode === "quick"
            ? "Drop a raw thought. Get LinkedIn + X content ready to publish."
            : "Give a topic or question. Get narrative angles with content generated for each."}
        </p>
      </div>

      {/* Mode toggle */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem" }}>
        <button style={S.modeBtn(mode === "quick")} onClick={() => setMode("quick")}>
          Quick Generate
        </button>
        <button style={S.modeBtn(mode === "research")} onClick={() => setMode("research")}>
          Research Mode
        </button>
      </div>

      {/* Mode content */}
      {mode === "quick" && <QuickGenerate />}
      {mode === "research" && <ResearchMode />}
    </div>
  );
}
