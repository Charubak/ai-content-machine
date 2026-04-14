import { useState, useEffect } from "react";
import Demo from "./pages/Demo";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import HowItWorks from "./pages/HowItWorks";
import WorkWithMe from "./pages/WorkWithMe";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export { API_BASE };

const NAV_ITEMS = [
  { id: "demo", label: "Live Demo" },
  { id: "onboarding", label: "Voice Setup" },
  { id: "dashboard", label: "Dashboard" },
  { id: "how", label: "How It Works" },
  { id: "hire", label: "Work With Me" },
];

export default function App() {
  const [page, setPage] = useState("demo");

  useEffect(() => {
    const handler = (e) => setPage(e.detail);
    window.addEventListener("navigate", handler);
    return () => window.removeEventListener("navigate", handler);
  }, []);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0908",
      color: "#c8c0b0",
      fontFamily: "'IBM Plex Mono', monospace",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500&family=Playfair+Display:wght@400;600;700&display=swap" rel="stylesheet" />

      {/* Navigation */}
      <nav style={{
        borderBottom: "1px solid rgba(245,166,35,0.15)",
        padding: "1rem 2rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        background: "rgba(10,9,8,0.95)",
        backdropFilter: "blur(8px)",
        zIndex: 100,
      }}>
        <div
          onClick={() => setPage("demo")}
          style={{ cursor: "pointer" }}
        >
          <span style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: "1.1rem",
            color: "#e8dcc8",
            fontWeight: 700,
          }}>
            Content Machine
          </span>
          <span style={{
            fontSize: "0.6rem",
            color: "rgba(245,166,35,0.5)",
            marginLeft: "0.5rem",
            letterSpacing: "0.1em",
          }}>
            by Charubak
          </span>
        </div>

        <div style={{ display: "flex", gap: "0.25rem" }}>
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              style={{
                background: page === item.id ? "rgba(245,166,35,0.1)" : "transparent",
                border: "none",
                borderBottom: page === item.id ? "1px solid #f5a623" : "1px solid transparent",
                color: page === item.id ? "#f5a623" : "rgba(200,192,176,0.45)",
                padding: "0.4rem 0.8rem",
                fontSize: "0.65rem",
                letterSpacing: "0.08em",
                cursor: "pointer",
                fontFamily: "'IBM Plex Mono', monospace",
                transition: "all 0.15s",
                textTransform: "uppercase",
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Pages */}
      <main>
        {page === "demo" && <Demo />}
        {page === "onboarding" && <Onboarding />}
        {page === "dashboard" && <Dashboard />}
        {page === "how" && <HowItWorks />}
        {page === "hire" && <WorkWithMe />}
      </main>

      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: rgba(245,166,35,0.25); }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}
