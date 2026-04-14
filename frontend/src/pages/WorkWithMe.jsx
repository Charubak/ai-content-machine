export default function WorkWithMe() {
  const S = {
    page: { maxWidth: 680, margin: "0 auto", padding: "3rem 1.5rem" },
    p: { fontSize: "0.78rem", color: "rgba(200,192,176,0.6)", lineHeight: 1.8 },
    label: { fontSize: "0.62rem", color: "rgba(245,166,35,0.55)", letterSpacing: "0.12em", marginBottom: "0.5rem", display: "block" },
    input: {
      width: "100%", background: "rgba(200,192,176,0.03)",
      border: "1px solid rgba(200,192,176,0.12)", color: "#c8c0b0",
      padding: "0.7rem", fontSize: "0.75rem",
      fontFamily: "'IBM Plex Mono', monospace", outline: "none",
      transition: "border-color 0.15s", marginBottom: "0.8rem",
    },
    textarea: {
      width: "100%", background: "rgba(200,192,176,0.03)",
      border: "1px solid rgba(200,192,176,0.12)", color: "#c8c0b0",
      padding: "0.7rem", fontSize: "0.75rem",
      fontFamily: "'IBM Plex Mono', monospace", resize: "vertical",
      outline: "none", lineHeight: 1.7, marginBottom: "0.8rem",
    },
  };

  const tiers = [
    {
      name: "Starter",
      price: "$1,500/mo",
      output: "12 posts/month",
      detail: "3 per week across LinkedIn + X",
      for: "Pre-seed protocols, solo founders",
    },
    {
      name: "Growth",
      price: "$3,000/mo",
      output: "25 posts/month",
      detail: "+ 1 LinkedIn long-form per week",
      for: "Seed to Series A, active communities",
      featured: true,
    },
    {
      name: "Scale",
      price: "$5,000/mo",
      output: "40 posts/month",
      detail: "+ Discord/Telegram community content",
      for: "Series A+, established protocols",
    },
  ];

  const includes = [
    "30-45 min voice onboarding session",
    "Custom Voice Document (versioned, tunable)",
    "Daily brief queue from curated feeds",
    "25-pattern AI quality gate on every post",
    "Weekly review dashboard",
    "Monthly voice tune based on performance data",
    "You approve everything before it publishes",
  ];

  return (
    <div style={S.page}>
      <div style={{ marginBottom: "2.5rem" }}>
        <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.15em", marginBottom: "0.5rem" }}>◆ DONE FOR YOU</div>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.7rem", color: "#e8dcc8", marginBottom: "0.8rem" }}>
          Work With Me
        </h1>
        <p style={S.p}>
          I run the content engine for you. You spend 2-3 hours per week reviewing and approving.
          Everything else, voice calibration, ideation, generation, quality gate, scheduling, I handle.
        </p>
      </div>

      {/* What's included */}
      <div style={{ marginBottom: "2.5rem" }}>
        <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.12em", marginBottom: "1rem" }}>WHAT'S INCLUDED</div>
        {includes.map((item, i) => (
          <div key={i} style={{ display: "flex", gap: "0.8rem", marginBottom: "0.5rem" }}>
            <span style={{ color: "#f5a623", fontSize: "0.7rem", flexShrink: 0 }}>▸</span>
            <span style={{ fontSize: "0.75rem", color: "rgba(200,192,176,0.65)" }}>{item}</span>
          </div>
        ))}
      </div>

      {/* Tiers */}
      <div style={{ marginBottom: "2.5rem" }}>
        <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.12em", marginBottom: "1rem" }}>PRICING</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          {tiers.map(tier => (
            <div key={tier.name} style={{
              border: `1px solid ${tier.featured ? "rgba(245,166,35,0.35)" : "rgba(200,192,176,0.1)"}`,
              background: tier.featured ? "rgba(245,166,35,0.04)" : "transparent",
              padding: "1rem 1.2rem",
              display: "flex", justifyContent: "space-between", alignItems: "center",
              flexWrap: "wrap", gap: "0.5rem",
            }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.2rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "#e8dcc8", fontWeight: 500 }}>{tier.name}</span>
                  {tier.featured && (
                    <span style={{ fontSize: "0.55rem", color: "#f5a623", border: "1px solid rgba(245,166,35,0.4)", padding: "0.1rem 0.4rem" }}>
                      MOST COMMON
                    </span>
                  )}
                </div>
                <div style={{ fontSize: "0.68rem", color: "rgba(200,192,176,0.5)" }}>{tier.output} · {tier.detail}</div>
                <div style={{ fontSize: "0.63rem", color: "rgba(200,192,176,0.35)", marginTop: "0.15rem" }}>{tier.for}</div>
              </div>
              <div style={{ fontFamily: "'Playfair Display', serif", fontSize: "1.1rem", color: "#f5a623" }}>
                {tier.price}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Contact */}
      <div style={{ borderTop: "1px solid rgba(200,192,176,0.08)", paddingTop: "2rem" }}>
        <div style={{ fontSize: "0.62rem", color: "rgba(245,166,35,0.5)", letterSpacing: "0.12em", marginBottom: "1rem" }}>GET IN TOUCH</div>
        <p style={{ ...S.p, marginBottom: "1.5rem" }}>
          First month includes voice onboarding and a 30-post pilot.
          If it doesn't work for you after 30 days, you pay nothing more.
        </p>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <a
            href="mailto:charubak.chakrabarti@gmail.com?subject=Content Machine Enquiry"
            style={{
              background: "rgba(245,166,35,0.1)",
              border: "1px solid rgba(245,166,35,0.4)",
              color: "#f5a623", padding: "0.65rem 1.4rem",
              fontSize: "0.7rem", letterSpacing: "0.1em",
              textDecoration: "none", fontFamily: "'IBM Plex Mono', monospace",
              display: "inline-block",
            }}
          >
            EMAIL ME →
          </a>
          <a
            href="https://linkedin.com/in/charubak"
            target="_blank" rel="noreferrer"
            style={{
              background: "transparent",
              border: "1px solid rgba(200,192,176,0.2)",
              color: "rgba(200,192,176,0.6)", padding: "0.65rem 1.4rem",
              fontSize: "0.7rem", letterSpacing: "0.1em",
              textDecoration: "none", fontFamily: "'IBM Plex Mono', monospace",
              display: "inline-block",
            }}
          >
            LINKEDIN
          </a>
        </div>
      </div>
    </div>
  );
}
