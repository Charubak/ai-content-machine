import { useState, useEffect } from "react";
import { API_BASE } from "../App";

const S = {
  page: { maxWidth: 900, margin: "0 auto", padding: "3rem 1.5rem" },
  label: { fontSize: "0.62rem", color: "rgba(245,166,35,0.55)", letterSpacing: "0.12em", marginBottom: "0.5rem", display: "block" },
  input: {
    width: "100%", background: "rgba(200,192,176,0.03)",
    border: "1px solid rgba(200,192,176,0.12)", color: "#c8c0b0",
    padding: "0.65rem", fontSize: "0.75rem",
    fontFamily: "'IBM Plex Mono', monospace", outline: "none", transition: "border-color 0.15s",
  },
  textarea: {
    width: "100%", background: "rgba(200,192,176,0.03)",
    border: "1px solid rgba(200,192,176,0.12)", color: "#c8c0b0",
    padding: "0.65rem", fontSize: "0.73rem",
    fontFamily: "'IBM Plex Mono', monospace", resize: "vertical", outline: "none", lineHeight: 1.7,
  },
  btn: (active) => ({
    background: active ? "rgba(245,166,35,0.1)" : "transparent",
    border: `1px solid ${active ? "rgba(245,166,35,0.4)" : "rgba(200,192,176,0.15)"}`,
    color: active ? "#f5a623" : "rgba(200,192,176,0.45)",
    padding: "0.4rem 0.8rem", fontSize: "0.65rem",
    letterSpacing: "0.08em", cursor: "pointer",
    fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.15s",
  }),
  card: {
    border: "1px solid rgba(200,192,176,0.1)",
    background: "rgba(200,192,176,0.02)",
    padding: "1rem", marginBottom: "0.6rem",
  },
};

const FORMATS = ["opinion", "reaction", "experience", "data", "narrative"];

function LoadingDots() {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {[0,1,2].map(i => (
        <div key={i} style={{ width: 5, height: 5, background: "#f5a623", borderRadius: "50%", animation: `pulse 1.2s ease ${i*0.2}s infinite` }} />
      ))}
    </div>
  );
}

function PostCard({ post, onStatusUpdate }) {
  const [expanded, setExpanded] = useState(false);
  const [activeVariant, setActiveVariant] = useState("linkedin_long");
  const [copied, setCopied] = useState(false);

  const variants = post.output || {};
  const variantKeys = Object.keys(variants).filter(k => k !== "community_message");

  const getContent = () => {
    if (activeVariant === "x_thread") return variants.x_thread?.join("\n\n") || "";
    return variants[activeVariant] || "";
  };

  const statusColor = {
    pending_review: "#f0ad4e",
    approved: "#5cb85c",
    rejected: "#d9534f",
    published: "#5bc0de"
  }[post.status] || "#c8c0b0";

  return (
    <div style={S.card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: expanded ? "0.8rem" : 0 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "0.68rem", color: "#e8dcc8", marginBottom: "0.2rem" }}>
            {post.brief?.topic || "Untitled"}
          </div>
          <div style={{ fontSize: "0.6rem", color: "rgba(200,192,176,0.4)" }}>
            {post.created_at?.slice(0, 10)} · {post.brief?.format}
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.6rem", color: statusColor, border: `1px solid ${statusColor}`, padding: "0.15rem 0.5rem" }}>
            {post.status?.replace("_", " ").toUpperCase()}
          </span>
          <button onClick={() => setExpanded(!expanded)} style={S.btn(expanded)}>
            {expanded ? "COLLAPSE" : "REVIEW"}
          </button>
        </div>
      </div>

      {expanded && (
        <div style={{ animation: "fadeUp 0.2s ease" }}>
          {/* Variant tabs */}
          <div style={{ display: "flex", borderBottom: "1px solid rgba(245,166,35,0.1)", marginBottom: "0" }}>
            {variantKeys.map(k => (
              <button key={k} onClick={() => setActiveVariant(k)} style={{
                background: "transparent", border: "none",
                borderBottom: activeVariant === k ? "2px solid #f5a623" : "2px solid transparent",
                color: activeVariant === k ? "#f5a623" : "rgba(200,192,176,0.35)",
                padding: "0.4rem 0.7rem", fontSize: "0.58rem",
                letterSpacing: "0.08em", cursor: "pointer",
                fontFamily: "'IBM Plex Mono', monospace",
                textTransform: "uppercase",
              }}>
                {k.replace("_", " ")}
              </button>
            ))}
          </div>

          <div style={{ border: "1px solid rgba(245,166,35,0.1)", borderTop: "none", padding: "1rem", marginBottom: "0.8rem" }}>
            <pre style={{ fontSize: "0.73rem", color: "#e8dcc8", whiteSpace: "pre-wrap", lineHeight: 1.8, margin: 0, fontFamily: "'IBM Plex Mono', monospace" }}>
              {getContent()}
            </pre>
            <button
              onClick={() => { navigator.clipboard?.writeText(getContent()); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
              style={{ ...S.btn(false), fontSize: "0.58rem", marginTop: "0.6rem" }}
            >
              {copied ? "COPIED ✓" : "COPY"}
            </button>
          </div>

          {/* Actions */}
          {post.status === "pending_review" && (
            <div style={{ display: "flex", gap: "0.4rem" }}>
              <button onClick={() => onStatusUpdate(post.post_id, "approved")} style={{ ...S.btn(false), color: "#5cb85c", borderColor: "rgba(92,184,92,0.3)" }}>
                ✓ APPROVE
              </button>
              <button onClick={() => onStatusUpdate(post.post_id, "rejected")} style={{ ...S.btn(false), color: "#d9534f", borderColor: "rgba(217,83,79,0.3)" }}>
                ✗ REJECT
              </button>
              <button onClick={() => onStatusUpdate(post.post_id, "published")} style={{ ...S.btn(false), color: "#5bc0de", borderColor: "rgba(91,192,222,0.3)" }}>
                ↑ MARK PUBLISHED
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [clientId, setClientId] = useState("");
  const [activeClientId, setActiveClientId] = useState("");
  const [activeTab, setActiveTab] = useState("generate");
  const [posts, setPosts] = useState([]);
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [genResult, setGenResult] = useState(null);
  const [error, setError] = useState(null);

  // Generate form
  const [topic, setTopic] = useState("");
  const [angle, setAngle] = useState("");
  const [format, setFormat] = useState("opinion");
  const [credential, setCredential] = useState("");
  const [dataPoint, setDataPoint] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [companyVoice, setCompanyVoice] = useState(false);

  const loadPosts = async (cid) => {
    if (!cid) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/posts/${cid}`);
      if (res.ok) {
        const data = await res.json();
        setPosts(data.posts || []);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const connect = () => {
    if (!clientId.trim()) return;
    setActiveClientId(clientId.trim());
    loadPosts(clientId.trim());
  };

  const generate = async () => {
    if (!activeClientId || !topic || !angle) return;
    setGenLoading(true);
    setGenResult(null);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: activeClientId,
          topic, angle, format, credential,
          data_point: dataPoint, source_text: sourceText,
          platform_priority: "both",
          company_voice: companyVoice,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      const data = await res.json();
      setGenResult(data);
      loadPosts(activeClientId);
    } catch (e) {
      setError(e.message);
    } finally {
      setGenLoading(false);
    }
  };

  const updateStatus = async (postId, status) => {
    await fetch(`${API_BASE}/posts/${activeClientId}/${postId}?status=${status}`, { method: "PATCH" });
    loadPosts(activeClientId);
  };

  const inp = (val, set) => ({ value: val, onChange: e => set(e.target.value) });
  const FOCUS = { borderColor: "rgba(245,166,35,0.35)" };
  const BLUR = { borderColor: "rgba(200,192,176,0.12)" };

  if (!activeClientId) {
    return (
      <div style={{ ...S.page, maxWidth: 500 }}>
        <div style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.15em", marginBottom: "0.5rem" }}>◆ DASHBOARD</div>
          <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.6rem", color: "#e8dcc8" }}>Content Dashboard</h1>
        </div>
        <span style={S.label}>ENTER CLIENT ID</span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <input
            style={S.input}
            value={clientId}
            onChange={e => setClientId(e.target.value)}
            onKeyDown={e => e.key === "Enter" && connect()}
            placeholder="e.g. charubak or client_abc123"
            onFocus={e => Object.assign(e.target.style, FOCUS)}
            onBlur={e => Object.assign(e.target.style, BLUR)}
          />
          <button onClick={connect} style={S.btn(true)}>CONNECT →</button>
        </div>
        <div style={{ marginTop: "0.8rem", fontSize: "0.63rem", color: "rgba(200,192,176,0.35)" }}>
          Client ID is created during Voice Setup onboarding.
        </div>
      </div>
    );
  }

  const TABS = ["generate", "review", "queue"];

  return (
    <div style={S.page}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "1.5rem" }}>
        <div>
          <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.15em", marginBottom: "0.3rem" }}>◆ DASHBOARD</div>
          <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.5rem", color: "#e8dcc8" }}>
            {activeClientId}
          </h1>
        </div>
        <button onClick={() => setActiveClientId("")} style={S.btn(false)}>SWITCH CLIENT</button>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid rgba(245,166,35,0.12)", marginBottom: "1.5rem" }}>
        {TABS.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            background: "transparent", border: "none",
            borderBottom: activeTab === tab ? "2px solid #f5a623" : "2px solid transparent",
            color: activeTab === tab ? "#f5a623" : "rgba(200,192,176,0.4)",
            padding: "0.5rem 1rem", fontSize: "0.63rem",
            letterSpacing: "0.1em", cursor: "pointer",
            fontFamily: "'IBM Plex Mono', monospace",
            textTransform: "uppercase",
          }}>
            {tab}
            {tab === "review" && posts.filter(p => p.status === "pending_review").length > 0 && (
              <span style={{ marginLeft: "0.4rem", background: "#f5a623", color: "#0a0908", borderRadius: "9px", padding: "0 5px", fontSize: "0.55rem" }}>
                {posts.filter(p => p.status === "pending_review").length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Generate */}
      {activeTab === "generate" && (
        <div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem", marginBottom: "0.8rem" }}>
            <div>
              <span style={S.label}>TOPIC</span>
              <input style={S.input} {...inp(topic, setTopic)} placeholder="What the post is about"
                onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
            </div>
            <div>
              <span style={S.label}>FORMAT</span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                {FORMATS.map(f => (
                  <button key={f} onClick={() => setFormat(f)} style={S.btn(format === f)}>{f}</button>
                ))}
              </div>
              <div style={{ marginTop: "0.8rem" }}>
                <span style={S.label}>VOICE</span>
                <div style={{ display: "flex", gap: "0.3rem" }}>
                  <button onClick={() => setCompanyVoice(false)} style={S.btn(!companyVoice)}>PERSONAL (I)</button>
                  <button onClick={() => setCompanyVoice(true)} style={S.btn(companyVoice)}>COMPANY (WE)</button>
                </div>
              </div>
            </div>
          </div>
          <div style={{ marginBottom: "0.8rem" }}>
            <span style={S.label}>ANGLE (the specific take or argument)</span>
            <textarea rows={3} style={S.textarea} {...inp(angle, setAngle)} placeholder="The specific take you want to make. The rougher the better."
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem", marginBottom: "0.8rem" }}>
            <div>
              <span style={S.label}>CREDENTIAL TO REFERENCE (optional)</span>
              <input style={S.input} {...inp(credential, setCredential)} placeholder="e.g. Forecastathon, mainnet launch"
                onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
            </div>
            <div>
              <span style={S.label}>DATA POINT TO INCLUDE (optional)</span>
              <input style={S.input} {...inp(dataPoint, setDataPoint)} placeholder="e.g. 300k NTN prize pool, 70k signups"
                onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
            </div>
          </div>
          <div style={{ marginBottom: "1rem" }}>
            <span style={S.label}>SOURCE TEXT TO REACT TO (optional, for reaction/narrative posts)</span>
            <textarea rows={3} style={S.textarea} {...inp(sourceText, setSourceText)} placeholder="Paste the article, tweet, or content you're reacting to"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>

          {error && <div style={{ color: "#ff6060", fontSize: "0.7rem", marginBottom: "0.8rem" }}>ERROR: {error}</div>}

          <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
            <button
              onClick={generate}
              disabled={genLoading || !topic || !angle}
              style={{
                ...S.btn(!genLoading && topic && angle),
                padding: "0.65rem 1.5rem", fontSize: "0.7rem",
                cursor: genLoading || !topic || !angle ? "not-allowed" : "pointer",
                opacity: genLoading || !topic || !angle ? 0.5 : 1,
              }}
            >
              {genLoading ? "GENERATING..." : "GENERATE ▶"}
            </button>
            {genLoading && <LoadingDots />}
          </div>

          {genResult && (
            <div style={{ marginTop: "1.5rem", border: "1px solid rgba(92,184,92,0.25)", padding: "1rem", animation: "fadeUp 0.3s ease" }}>
              <div style={{ fontSize: "0.62rem", color: "#5cb85c", letterSpacing: "0.1em", marginBottom: "0.5rem" }}>
                ◆ GENERATED · Post ID: {genResult.post_id} · Gate: {genResult.passed_gate ? "✓ PASSED" : "⚠ REVIEW"}
              </div>
              <div style={{ fontSize: "0.7rem", color: "rgba(200,192,176,0.5)" }}>
                Post saved to review queue.
              </div>
            </div>
          )}
        </div>
      )}

      {/* Review */}
      {activeTab === "review" && (
        <div>
          {loading && <LoadingDots />}
          {!loading && posts.length === 0 && (
            <div style={{ fontSize: "0.72rem", color: "rgba(200,192,176,0.35)" }}>No posts yet. Generate some content first.</div>
          )}
          {posts.map(post => (
            <PostCard key={post.post_id} post={post} onStatusUpdate={updateStatus} />
          ))}
        </div>
      )}

      {/* Queue (brief suggestions from RSS) */}
      {activeTab === "queue" && (
        <div>
          <div style={{ fontSize: "0.72rem", color: "rgba(200,192,176,0.4)", lineHeight: 1.7 }}>
            Brief suggestions from the RSS monitor appear here. Run the monitor script to populate this queue.
            <br />
            <code style={{ fontSize: "0.65rem", color: "#f5a623" }}>
              python backend/inputs/rss_monitor.py {activeClientId}
            </code>
          </div>
        </div>
      )}
    </div>
  );
}
