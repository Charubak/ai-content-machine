import { useState } from "react";
import { API_BASE } from "../App";

const S = {
  page: { maxWidth: 720, margin: "0 auto", padding: "3rem 1.5rem" },
  label: { fontSize: "0.62rem", color: "rgba(245,166,35,0.55)", letterSpacing: "0.12em", marginBottom: "0.5rem", display: "block" },
  input: {
    width: "100%", background: "rgba(200,192,176,0.03)",
    border: "1px solid rgba(200,192,176,0.12)", color: "#c8c0b0",
    padding: "0.7rem", fontSize: "0.78rem",
    fontFamily: "'IBM Plex Mono', monospace", outline: "none",
    transition: "border-color 0.15s",
  },
  textarea: {
    width: "100%", background: "rgba(200,192,176,0.03)",
    border: "1px solid rgba(200,192,176,0.12)", color: "#c8c0b0",
    padding: "0.7rem", fontSize: "0.75rem",
    fontFamily: "'IBM Plex Mono', monospace",
    resize: "vertical", outline: "none", lineHeight: 1.7,
    transition: "border-color 0.15s",
  },
  btn: (active) => ({
    background: active ? "rgba(245,166,35,0.12)" : "transparent",
    border: `1px solid ${active ? "rgba(245,166,35,0.5)" : "rgba(200,192,176,0.15)"}`,
    color: active ? "#f5a623" : "rgba(200,192,176,0.5)",
    padding: "0.4rem 0.85rem", fontSize: "0.67rem",
    letterSpacing: "0.08em", cursor: "pointer",
    fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.15s",
  }),
  primaryBtn: (disabled) => ({
    background: disabled ? "rgba(245,166,35,0.04)" : "rgba(245,166,35,0.12)",
    border: `1px solid ${disabled ? "rgba(245,166,35,0.15)" : "rgba(245,166,35,0.5)"}`,
    color: disabled ? "rgba(245,166,35,0.25)" : "#f5a623",
    padding: "0.65rem 1.5rem", fontSize: "0.7rem",
    letterSpacing: "0.1em", cursor: disabled ? "not-allowed" : "pointer",
    fontFamily: "'IBM Plex Mono', monospace", transition: "all 0.15s",
  }),
  field: { marginBottom: "1.2rem" },
};

const TONES = ["degen", "hybrid", "institutional", "founder"];
const FOCUS = { borderColor: "rgba(245,166,35,0.35)" };
const BLUR = { borderColor: "rgba(200,192,176,0.12)" };

const STAGES = [
  { id: 1, label: "Identity", desc: "Brand basics" },
  { id: 2, label: "Samples", desc: "Writing examples" },
  { id: 3, label: "Rules", desc: "Voice rules" },
  { id: 4, label: "Test", desc: "Calibration" },
];

function StageIndicator({ current }) {
  return (
    <div style={{ display: "flex", gap: "0", marginBottom: "2.5rem" }}>
      {STAGES.map((s, i) => (
        <div key={s.id} style={{ flex: 1, display: "flex", alignItems: "center" }}>
          <div style={{ flex: 1 }}>
            <div style={{
              padding: "0.6rem 0.8rem",
              background: s.id === current ? "rgba(245,166,35,0.1)" : "transparent",
              borderTop: `2px solid ${s.id <= current ? "#f5a623" : "rgba(200,192,176,0.15)"}`,
            }}>
              <div style={{ fontSize: "0.6rem", color: s.id <= current ? "#f5a623" : "rgba(200,192,176,0.3)", letterSpacing: "0.1em" }}>
                STEP {s.id}
              </div>
              <div style={{ fontSize: "0.72rem", color: s.id === current ? "#e8dcc8" : "rgba(200,192,176,0.4)" }}>
                {s.label}
              </div>
            </div>
          </div>
          {i < STAGES.length - 1 && (
            <div style={{ width: "1rem", height: "1px", background: "rgba(200,192,176,0.1)" }} />
          )}
        </div>
      ))}
    </div>
  );
}

function TagInput({ label, value, onChange, placeholder }) {
  const [input, setInput] = useState("");

  const add = () => {
    const trimmed = input.trim();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
      setInput("");
    }
  };

  return (
    <div style={S.field}>
      <span style={S.label}>{label}</span>
      <div style={{ display: "flex", gap: "0.4rem", marginBottom: "0.5rem" }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder={placeholder}
          style={{ ...S.input, flex: 1 }}
          onFocus={e => Object.assign(e.target.style, FOCUS)}
          onBlur={e => Object.assign(e.target.style, BLUR)}
        />
        <button onClick={add} style={S.btn(false)}>ADD</button>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
        {value.map(tag => (
          <span key={tag} style={{
            background: "rgba(245,166,35,0.08)",
            border: "1px solid rgba(245,166,35,0.2)",
            color: "#f5a623", padding: "0.2rem 0.6rem",
            fontSize: "0.65rem", display: "flex", alignItems: "center", gap: "0.4rem",
          }}>
            {tag}
            <span
              onClick={() => onChange(value.filter(t => t !== tag))}
              style={{ cursor: "pointer", color: "rgba(245,166,35,0.5)" }}
            >×</span>
          </span>
        ))}
      </div>
    </div>
  );
}

export default function Onboarding() {
  const [stage, setStage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Stage 1
  const [brandName, setBrandName] = useState("");
  const [oneLiner, setOneLiner] = useState("");
  const [audience, setAudience] = useState("");
  const [competitorRespect, setCompetitorRespect] = useState("");
  const [competitorDislike, setCompetitorDislike] = useState("");

  // Stage 2
  const [samples, setSamples] = useState("");
  const [bestPost1, setBestPost1] = useState({ text: "", why: "" });
  const [bestPost2, setBestPost2] = useState({ text: "", why: "" });
  const [rawAuthentic, setRawAuthentic] = useState("");
  const [contentHate, setContentHate] = useState([]);

  // Stage 3
  const [tone, setTone] = useState("hybrid");
  const [ownedTopics, setOwnedTopics] = useState([]);
  const [avoidedTopics, setAvoidedTopics] = useState([]);
  const [bannedWords, setBannedWords] = useState([]);
  const [requiredPhrases, setRequiredPhrases] = useState([]);
  const [alwaysTrue, setAlwaysTrue] = useState("");

  // Stage 4
  const [testThought, setTestThought] = useState("");
  const [testResult, setTestResult] = useState(null);
  const [calibrationNotes, setCalibrationNotes] = useState("");

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const bestPosts = [bestPost1, bestPost2]
        .filter(p => p.text.trim())
        .map(p => ({ text: p.text, why_it_worked: p.why }));

      const writingSamples = [samples, rawAuthentic].filter(Boolean);

      const res = await fetch(`${API_BASE}/onboard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          brand_name: brandName,
          one_liner: oneLiner,
          target_audience: audience,
          tone_position: tone,
          owned_topics: ownedTopics,
          avoided_topics: avoidedTopics,
          banned_words: bannedWords,
          required_phrases: requiredPhrases,
          always_true: alwaysTrue,
          competitor_respect: competitorRespect,
          competitor_dislike: competitorDislike,
          writing_samples: writingSamples,
          best_posts: bestPosts,
          content_hate: contentHate,
          calibration_notes: calibrationNotes,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Onboarding failed");
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const inp = (val, set) => ({
    value: val, onChange: e => set(e.target.value),
    onFocus: e => Object.assign(e.target.style, FOCUS),
    onBlur: e => Object.assign(e.target.style, BLUR),
  });

  if (result) {
    return (
      <div style={S.page}>
        <div style={{ border: "1px solid rgba(245,166,35,0.25)", padding: "2rem", animation: "fadeUp 0.4s ease" }}>
          <div style={{ fontSize: "0.62rem", color: "#f5a623", letterSpacing: "0.12em", marginBottom: "1rem" }}>
            ◆ VOICE DOCUMENT CREATED
          </div>
          <div style={{ fontSize: "0.75rem", color: "rgba(200,192,176,0.5)", marginBottom: "0.4rem" }}>
            Client ID: <span style={{ color: "#f5a623" }}>{result.client_id}</span> · Version {result.version}
          </div>
          <div style={{ fontSize: "0.78rem", color: "#e8dcc8", marginBottom: "1.5rem" }}>
            {result.voice_document?.split('\n').slice(0, 8).join('\n')}...
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={() => navigator.clipboard?.writeText(result.client_id)} style={S.btn(false)}>
              COPY CLIENT ID
            </button>
            <button onClick={() => setResult(null)} style={S.btn(false)}>
              NEW ONBOARDING
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={S.page}>
      <div style={{ marginBottom: "2rem" }}>
        <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.15em", marginBottom: "0.5rem" }}>◆ VOICE SETUP</div>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.6rem", color: "#e8dcc8", marginBottom: "0.5rem" }}>
          Client Onboarding
        </h1>
        <p style={{ fontSize: "0.72rem", color: "rgba(200,192,176,0.45)", lineHeight: 1.6 }}>
          30-45 minutes to build a Voice Document that makes every generated post sound like this specific human.
        </p>
      </div>

      <StageIndicator current={stage} />

      {/* Stage 1: Identity */}
      {stage === 1 && (
        <div style={{ animation: "fadeUp 0.3s ease" }}>
          <div style={S.field}>
            <span style={S.label}>BRAND OR PERSON NAME</span>
            <input style={S.input} {...inp(brandName, setBrandName)} placeholder="e.g. Aave, Hyperliquid, John Smith"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <div style={S.field}>
            <span style={S.label}>WHAT THEY DO IN ONE SENTENCE</span>
            <input style={S.input} {...inp(oneLiner, setOneLiner)} placeholder="Not the whitepaper version. Plain English."
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <div style={S.field}>
            <span style={S.label}>TARGET AUDIENCE</span>
            <input style={S.input} {...inp(audience, setAudience)} placeholder="Who reads this? What do they care about?"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem" }}>
            <div style={S.field}>
              <span style={S.label}>COMPETITOR THEY RESPECT</span>
              <input style={S.input} {...inp(competitorRespect, setCompetitorRespect)} placeholder="Study their tone"
                onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
            </div>
            <div style={S.field}>
              <span style={S.label}>COMPETITOR THEY DISLIKE</span>
              <input style={S.input} {...inp(competitorDislike, setCompetitorDislike)} placeholder="Avoid this register"
                onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
            </div>
          </div>
        </div>
      )}

      {/* Stage 2: Samples */}
      {stage === 2 && (
        <div style={{ animation: "fadeUp 0.3s ease" }}>
          <div style={S.field}>
            <span style={S.label}>PASTE RECENT ARTICLES OR POSTS (combine multiple, separate with ---)</span>
            <textarea rows={6} style={S.textarea} {...inp(samples, setSamples)}
              placeholder="Paste any writing samples here. The more the better."
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <div style={S.field}>
            <span style={S.label}>BEST PERFORMING POST #1 — and why it worked</span>
            <textarea rows={4} style={{ ...S.textarea, marginBottom: "0.4rem" }}
              value={bestPost1.text} onChange={e => setBestPost1(p => ({ ...p, text: e.target.value }))}
              placeholder="Paste the post text"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
            <input style={S.input} value={bestPost1.why} onChange={e => setBestPost1(p => ({ ...p, why: e.target.value }))}
              placeholder="Why did it work? (optional)"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <div style={S.field}>
            <span style={S.label}>BEST PERFORMING POST #2</span>
            <textarea rows={4} style={{ ...S.textarea, marginBottom: "0.4rem" }}
              value={bestPost2.text} onChange={e => setBestPost2(p => ({ ...p, text: e.target.value }))}
              placeholder="Paste the post text"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
            <input style={S.input} value={bestPost2.why} onChange={e => setBestPost2(p => ({ ...p, why: e.target.value }))}
              placeholder="Why did it work? (optional)"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <div style={S.field}>
            <span style={S.label}>RAW WRITING THAT FELT AUTHENTIC (even if it never got engagement)</span>
            <textarea rows={4} style={S.textarea} {...inp(rawAuthentic, setRawAuthentic)}
              placeholder="Unpolished but felt real. Discord messages, internal docs, anything."
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          <TagInput
            label="CONTENT THEY NEVER WANT TO PRODUCE"
            value={contentHate}
            onChange={setContentHate}
            placeholder="e.g. hype posts, FUD responses, price predictions"
          />
        </div>
      )}

      {/* Stage 3: Rules */}
      {stage === 3 && (
        <div style={{ animation: "fadeUp 0.3s ease" }}>
          <div style={S.field}>
            <span style={S.label}>TONE POSITION</span>
            <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
              {TONES.map(t => (
                <button key={t} onClick={() => setTone(t)} style={S.btn(tone === t)}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <TagInput label="TOPICS THEY OWN (5-7)" value={ownedTopics} onChange={setOwnedTopics}
            placeholder="e.g. DeFi growth mechanics" />
          <TagInput label="TOPICS TO AVOID" value={avoidedTopics} onChange={setAvoidedTopics}
            placeholder="e.g. price predictions, competitor attacks" />
          <TagInput label="ADDITIONAL BANNED WORDS (beyond defaults)" value={bannedWords} onChange={setBannedWords}
            placeholder="e.g. community, ecosystem (when vague)" />
          <TagInput label="PHRASES THEY ALWAYS USE" value={requiredPhrases} onChange={setRequiredPhrases}
            placeholder="e.g. specific product names, preferred terms" />
          <div style={S.field}>
            <span style={S.label}>ALWAYS TRUE ABOUT THIS CONTENT (free text)</span>
            <textarea rows={3} style={S.textarea} {...inp(alwaysTrue, setAlwaysTrue)}
              placeholder="What should always be true? e.g. 'Always grounded in on-chain data. Never makes claims without receipts.'"
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
        </div>
      )}

      {/* Stage 4: Test */}
      {stage === 4 && (
        <div style={{ animation: "fadeUp 0.3s ease" }}>
          <p style={{ fontSize: "0.75rem", color: "rgba(200,192,176,0.5)", lineHeight: 1.7, marginBottom: "1.5rem" }}>
            Submit the Voice Document, then test it with a sample post. Read it together with the client and note what's right and what's off.
          </p>
          <div style={S.field}>
            <span style={S.label}>CALIBRATION NOTES (what should the system always remember?)</span>
            <textarea rows={3} style={S.textarea} {...inp(calibrationNotes, setCalibrationNotes)}
              placeholder="Any final notes from the session before we lock the voice document."
              onFocus={e => Object.assign(e.target.style, FOCUS)} onBlur={e => Object.assign(e.target.style, BLUR)} />
          </div>
          {error && (
            <div style={{ border: "1px solid rgba(255,80,80,0.25)", padding: "0.7rem", marginBottom: "1rem" }}>
              <span style={{ color: "#ff6060", fontSize: "0.7rem" }}>ERROR: {error}</span>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "2rem", paddingTop: "1.5rem", borderTop: "1px solid rgba(200,192,176,0.08)" }}>
        <button
          onClick={() => setStage(s => s - 1)}
          disabled={stage === 1}
          style={S.btn(false)}
        >
          ← BACK
        </button>
        {stage < 4 ? (
          <button onClick={() => setStage(s => s + 1)} style={S.btn(true)}>
            NEXT →
          </button>
        ) : (
          <button onClick={submit} disabled={loading} style={S.primaryBtn(loading)}>
            {loading ? "BUILDING VOICE..." : "CREATE VOICE DOCUMENT ▶"}
          </button>
        )}
      </div>
    </div>
  );
}
