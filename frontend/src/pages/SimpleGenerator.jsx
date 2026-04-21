import { useState } from "react";
import { API_BASE } from "../App";

const S = {
  page: {
    maxWidth: 760,
    margin: "0 auto",
    padding: "3rem 1.5rem",
  },
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
  tweetBox: {
    borderLeft: "2px solid rgba(245,166,35,0.2)",
    paddingLeft: "0.9rem",
    marginBottom: "0.85rem",
    fontSize: "0.8rem",
    lineHeight: 1.65,
    color: "#c8c0b0",
  },
  tweetNum: {
    fontSize: "0.55rem",
    color: "rgba(245,166,35,0.3)",
    letterSpacing: "0.1em",
    display: "block",
    marginBottom: "0.25rem",
  },
  error: {
    border: "1px solid rgba(217,83,79,0.3)",
    background: "rgba(217,83,79,0.05)",
    color: "rgba(217,83,79,0.8)",
    padding: "0.8rem",
    fontSize: "0.75rem",
    marginTop: "1rem",
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
};

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
            width: 4,
            height: 4,
            background: "#f5a623",
            borderRadius: "50%",
            animation: `pulse 1s ease ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </span>
  );
}

export default function SimpleGenerator() {
  const [idea, setIdea] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [xTab, setXTab] = useState("thread"); // "thread" | "single"

  const canGenerate = idea.trim().length > 10 && !loading;

  async function generate() {
    if (!canGenerate) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_thought: idea.trim(), tone: "founder" }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Error ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message || "Generation failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={{ marginBottom: "2.5rem", animation: "fadeUp 0.4s ease" }}>
        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: "1.8rem",
          color: "#e8dcc8",
          fontWeight: 600,
          marginBottom: "0.5rem",
        }}>
          Idea to post.
        </h1>
        <p style={{
          fontSize: "0.78rem",
          color: "rgba(200,192,176,0.45)",
          lineHeight: 1.6,
        }}>
          Drop a raw thought. Get a LinkedIn post and X thread ready to publish.
          No setup. No configuration.
        </p>
      </div>

      {/* Input */}
      <div style={{ marginBottom: "1.5rem" }}>
        <label style={S.label}>Your idea</label>
        <textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="e.g. Most Web3 projects fail not because the tech is wrong but because they ship the product before they've built any trust with the community that needs to believe in it."
          rows={5}
          style={S.textarea}
          onFocus={(e) => (e.target.style.borderColor = "rgba(245,166,35,0.35)")}
          onBlur={(e) => (e.target.style.borderColor = "rgba(200,192,176,0.12)")}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") generate();
          }}
        />
        <div style={{
          fontSize: "0.58rem",
          color: "rgba(200,192,176,0.25)",
          marginTop: "0.4rem",
        }}>
          ⌘ + Enter to generate
        </div>
      </div>

      {/* Generate button */}
      <button
        onClick={generate}
        disabled={!canGenerate}
        style={S.runBtn(!canGenerate)}
      >
        {loading ? <><LoadingDots />&nbsp;&nbsp;GENERATING</> : "GENERATE CONTENT"}
      </button>

      {error && <div style={S.error}>{error}</div>}

      {/* Output */}
      {result && (
        <div style={{ marginTop: "2.5rem" }}>
          <div style={{
            fontSize: "0.58rem",
            color: "rgba(245,166,35,0.3)",
            letterSpacing: "0.15em",
            marginBottom: "1.5rem",
          }}>
            OUTPUT — READY TO PUBLISH
          </div>

          {/* LinkedIn long */}
          <div style={S.card}>
            <div style={S.cardTitle}>
              <span>LinkedIn — Long-form</span>
              <CopyBtn text={result.linkedin_long} />
            </div>
            <div style={S.text}>{result.linkedin_long}</div>
          </div>

          {/* LinkedIn short */}
          <div style={S.card}>
            <div style={S.cardTitle}>
              <span>LinkedIn — Short</span>
              <CopyBtn text={result.linkedin_short} />
            </div>
            <div style={S.text}>{result.linkedin_short}</div>
          </div>

          {/* X output with tabs */}
          <div style={S.card}>
            <div style={S.cardTitle}>
              <span>X / Twitter</span>
              <CopyBtn
                text={
                  xTab === "thread"
                    ? result.x_thread.join("\n\n")
                    : result.x_single
                }
              />
            </div>

            {/* Tabs */}
            <div style={{
              display: "flex",
              gap: "0.1rem",
              borderBottom: "1px solid rgba(200,192,176,0.08)",
              marginBottom: "1.2rem",
            }}>
              <button style={S.tab(xTab === "thread")} onClick={() => setXTab("thread")}>
                Thread
              </button>
              <button style={S.tab(xTab === "single")} onClick={() => setXTab("single")}>
                Single Tweet
              </button>
            </div>

            {xTab === "thread" && (
              <div>
                {result.x_thread.map((tweet, i) => (
                  <div key={i} style={S.tweetBox}>
                    <span style={S.tweetNum}>{i + 1} / {result.x_thread.length}</span>
                    {tweet}
                  </div>
                ))}
              </div>
            )}

            {xTab === "single" && (
              <div style={{ ...S.text, color: "#e8dcc8" }}>{result.x_single}</div>
            )}
          </div>

          {/* Score bar */}
          {(result.score_before != null || result.score_after != null) && (
            <div style={{
              display: "flex",
              gap: "2rem",
              padding: "0.8rem 0",
              borderTop: "1px solid rgba(200,192,176,0.06)",
              marginTop: "0.5rem",
            }}>
              {[
                { label: "RAW SCORE", val: result.score_before },
                { label: "AFTER GATE", val: result.score_after },
              ].map(({ label, val }) => {
                const color = val <= 3 ? "#5cb85c" : val <= 6 ? "#f0ad4e" : "#d9534f";
                return (
                  <div key={label} style={{ textAlign: "center" }}>
                    <div style={{ fontSize: "0.52rem", color: "rgba(200,192,176,0.3)", letterSpacing: "0.1em" }}>
                      {label}
                    </div>
                    <div style={{
                      fontSize: "1.4rem",
                      fontFamily: "'Playfair Display', serif",
                      color,
                      lineHeight: 1.1,
                    }}>
                      {val}
                    </div>
                  </div>
                );
              })}
              <div style={{
                fontSize: "0.7rem",
                color: "rgba(200,192,176,0.3)",
                alignSelf: "center",
                paddingLeft: "0.5rem",
              }}>
                /10 slop score — lower is better
              </div>
            </div>
          )}

          {/* Reset */}
          <button
            onClick={() => { setResult(null); setIdea(""); }}
            style={{
              background: "transparent",
              border: "none",
              color: "rgba(200,192,176,0.25)",
              fontSize: "0.62rem",
              letterSpacing: "0.08em",
              cursor: "pointer",
              fontFamily: "'IBM Plex Mono', monospace",
              marginTop: "1.5rem",
              padding: "0",
              textDecoration: "underline",
            }}
          >
            ← New idea
          </button>
        </div>
      )}
    </div>
  );
}
