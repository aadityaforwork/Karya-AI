"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Health, Skill } from "../../lib/types";

const TIER_ROLE = ["cheap · tried first", "mid · on escalation", "frontier · hard cases"];
const LANGS = [
  { l: "English", acc: "88%", to: "Tier 0 (cheap)", badge: "mint" },
  { l: "Hindi", acc: "72%", to: "Tier 0, watched", badge: "amber" },
  { l: "Marathi / Telugu", acc: "40%", to: "Starts smart (tier 1+)", badge: "rose" },
];

export default function SettingsPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    api.skills().then((r) => setSkills(r.skills)).catch(() => {});
  }, []);

  return (
    <div className="page">
      <div className="lead">
        <h1>Settings</h1>
        <p>How the workforce is configured. The engine, the cost ladder, the trust rules, and the skill catalogue.</p>
      </div>

      <div className="split flush">
        <div className="card">
          <div className="hd"><h3>Engine &amp; model tiers</h3></div>
          <div className="bd">
            <div className="minirow"><span>Engine</span><span><span className={`badge ${health?.engine === "openai" ? "mint" : "slate"}`}>{health?.engine || "…"}</span></span></div>
            <div className="minirow"><span>Confidence gate (τ)</span><span className="mono">{health?.gate_tau ?? "…"}</span></div>
            <div className="section-gap">
              {(health?.tiers || []).map((t) => (
                <div className="barline row-mid" key={t.tier}>
                  <span><b>Tier {t.tier}</b> <span className="mono muted">{t.model}</span></span>
                  <span className="tierrole">{TIER_ROLE[t.tier]}</span>
                </div>
              ))}
            </div>
            <p className="note">
              Set <span className="mono">OPENAI_API_KEY</span> in the backend <span className="mono">.env</span> to switch from mock to live. Tiers run through LangChain.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="hd"><h3>Trust &amp; approval policy</h3></div>
          <div className="bd">
            <div className="minirow"><span>Evidence required</span><span className="badge mint">every claim</span></div>
            <div className="minirow"><span>Unproven claims</span><span className="badge rose">rejected</span></div>
            <div className="minirow"><span>External sends</span><span className="badge amber">human approval</span></div>
            <div className="minirow"><span>Duplicate sends</span><span className="badge slate">blocked (idempotent)</span></div>
            <p className="note">
              Karya runs the boring 95% autonomously; anything with real, irreversible consequences waits in Approvals.
            </p>
          </div>
        </div>
      </div>

      <div className="card card-gap">
        <div className="hd"><h3>Language-aware routing</h3></div>
        <div className="bd">
          <table className="langtable">
            <thead><tr><th>Language</th><th>Cheap-model accuracy</th><th>Routed to</th></tr></thead>
            <tbody>
              {LANGS.map((r) => (
                <tr key={r.l}><td>{r.l}</td><td><span className={`badge ${r.badge}`}>{r.acc}</span></td><td className="mono">{r.to}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card card-gap">
        <div className="hd"><h3>Skill catalogue</h3></div>
        <div className="bd">
          {skills.map((s) => (
            <div className="minirow" key={s.id}>
              <span><b>{s.name}</b> <span className="muted">· {s.tagline}</span></span>
              <span>{s.active ? <span className="badge mint">live</span> : <span className="badge slate">soon</span>}</span>
            </div>
          ))}
          <p className="note">
            Browse the underlying data pool on the <a href="/talent">Talent</a> page.
          </p>
        </div>
      </div>
    </div>
  );
}
