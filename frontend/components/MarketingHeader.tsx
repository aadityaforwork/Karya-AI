"use client";

import { useAuth } from "../lib/auth";

// N5 floating pill — detached from the viewport edge, blur backdrop over
// the dark canvas. Deliberately a different register from the app's N3
// side rail: this is the public front door, not the signed-in workbench.
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
        <a className="btn" href="/app">Open app <span aria-hidden>→</span></a>
      ) : (
        <div className="navcta">
          <a className="btn ghost" href="/login">Log in</a>
          <a className="btn" href="/signup">Start free</a>
        </div>
      ))}
    </nav>
  );
}
