"use client";

import { useAuth } from "../lib/auth";

export default function MarketingHeader() {
  const { user, loading } = useAuth();
  return (
    <nav className="nav">
      <a className="brand" href="/"><span className="mark">का</span>Karya</a>
      <div className="links">
        <a href="/#how">How it works</a>
        <a href="/#skills">Skills</a>
        <a href="/pricing">Pricing</a>
      </div>
      <span className="spacer" />
      {!loading && (user ? (
        <a className="btn" style={{ padding: "8px 16px" }} href="/app">Open app →</a>
      ) : (
        <span style={{ display: "flex", gap: 8 }}>
          <a className="btn ghost" style={{ padding: "8px 16px" }} href="/login">Log in</a>
          <a className="btn" style={{ padding: "8px 16px" }} href="/signup">Start free</a>
        </span>
      ))}
    </nav>
  );
}
