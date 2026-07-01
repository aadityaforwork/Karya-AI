"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { SKILL_ACCENT } from "../lib/useSkills";
import type { Plan, Skill } from "../lib/types";
import { Check, Cross, Shield } from "../components/icons";

const PILLARS = [
  { t: "The cheapest model that can be trusted", d: "Every task starts on a cheap model and escalates to a smarter one only when the model itself is unsure. You pay expert prices for the hard parts alone, about an eighth of frontier-only cost." },
  { t: "No claim without proof", d: "A worker cannot say a thing unless a real source line entails it. The exact resume or company line is cited, and anything unproven is dropped before it is ever saved or shown." },
  { t: "A human approves what matters", d: "Karya does the routine 95% on its own. Anything with real consequences, an external send, waits for your one-tap approval, every draft shown with its evidence." },
];

const STEPS = [
  { n: "1", t: "Describe the outcome", d: "“Hire 2 backend engineers in Pune.” You state the goal, not the steps." },
  { n: "2", t: "Watch the team work", d: "A live feed shows sourcing, evidence-grounded screening, and drafting, in any language." },
  { n: "3", t: "Approve in one tap", d: "Review the final messages with the proof shown. You stay in control of every send." },
  { n: "4", t: "It keeps the conversation going", d: "When a reply lands, Karya answers grounded in proven facts and never invents a commitment." },
];

export default function LandingPage() {
  const { user } = useAuth();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);

  useEffect(() => {
    api.skills().then((r) => setSkills(r.skills)).catch(() => {});
    api.plans().then((r) => setPlans(r.plans)).catch(() => {});
  }, []);

  const cta = user ? "/app" : "/signup";

  return (
    <div>
      <section className="hero">
        <div className="hero-inner">
          <span className="pill">Describe the outcome, not the steps</span>
          <h1>An AI workforce that<br />does the job, <span className="hl">with proof.</span></h1>
          <p>Describe an outcome and a team of AI workers does the whole job: sourced, screened with every claim grounded in evidence, contacted and booked, cheaply, in any language.</p>
          <div className="hero-cta">
            <a className="btn" href={cta}>{user ? "Open your workspace" : "Start free"}</a>
            <a className="btn ghost" href="/login">Try the live demo</a>
          </div>

          <div className="heroproof">
            <div className="hp-head">
              <span><Shield size={13} /> Trust gate</span>
              <span className="mono">screening · Priya Sharma</span>
            </div>
            <div className="proofrow ok">
              <span className="ic"><Check size={13} /></span>
              <span className="pt">Operates in fintech</span>
              <span className="cite mono">L1 cited</span>
            </div>
            <div className="proofrow no">
              <span className="ic"><Cross size={13} /></span>
              <span className="pt">Series B funded</span>
              <span className="cite mono">no evidence, dropped</span>
            </div>
            <div className="hp-foot mono">tier 0 to tier 2 on doubt · 0.91 confident · $0.0007</div>
          </div>

          <div className="hero-stats">
            <div><b>~8x</b><span>cheaper than frontier-only</span></div>
            <div><b>0</b><span>unproven claims kept</span></div>
            <div><b>4+</b><span>Indian languages routed</span></div>
          </div>
        </div>
      </section>

      <div className="page" style={{ paddingTop: 10 }}>
        <section className="msection">
          <h2 className="mtitle">Why AI has not done real work yet</h2>
          <p className="msub">Most agents are confident and wrong, and bill you frontier rates to be so. Karya fixes both.</p>
          <div className="rules">
            {PILLARS.map((p) => (
              <div className="card" key={p.t}><div className="bd">
                <div style={{ fontWeight: 650, marginBottom: 6 }}>{p.t}</div>
                <div style={{ color: "var(--muted)", fontSize: 13.5 }}>{p.d}</div>
              </div></div>
            ))}
          </div>
        </section>

        <section className="msection">
          <h2 className="mtitle">The conversation stays grounded too</h2>
          <p className="msub">Most tools stop thinking after the first message. Karya runs the reply on the same trust engine.</p>
          <div className="convo">
            <div className="cv-msg in">
              <div className="who">candidate</div>
              Does this role actually use Kubernetes day to day, and is there any Rust on the team? I only move for the right stack.
            </div>
            <div className="cv-msg out">
              <div className="who"><Shield size={11} /> karya, grounded</div>
              Yes, Kubernetes is part of this role, it is in the spec. I cannot confirm Rust is in scope, so I will not claim it, let me check with the team and come back to you.
            </div>
            <div className="cv-tags">
              <span className="gchip">confirmed: kubernetes</span>
              <span className="rchip">refused: rust</span>
            </div>
          </div>
        </section>

        <section className="msection" id="skills">
          <h2 className="mtitle">One platform, many skills</h2>
          <p className="msub">One engine runs every skill: cost-aware routing, an evidence verifier, an approval gate.</p>
          <div className="rolegrid">
            {skills.map((s) => (
              <div className="rolecard" key={s.id} style={{ opacity: s.active ? 1 : 0.55, borderLeft: `4px solid ${SKILL_ACCENT[s.accent] || "var(--ink)"}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div className="rt">{s.name}</div>
                  {s.active ? <span className="badge mint">live</span> : <span className="badge slate">soon</span>}
                </div>
                <div className="rm" style={{ marginTop: 4 }}>{s.tagline}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="msection" id="how">
          <h2 className="mtitle">What it feels like</h2>
          <div className="steps">
            {STEPS.map((s) => (
              <div className="step-card" key={s.n}>
                <div className="step-n">{s.n}</div>
                <div style={{ fontWeight: 650, margin: "8px 0 4px" }}>{s.t}</div>
                <div style={{ color: "var(--muted)", fontSize: 13 }}>{s.d}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="msection" id="pricing">
          <h2 className="mtitle">Simple, honest pricing</h2>
          <div className="rolegrid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            {plans.map((p) => (
              <div className="card" key={p.id}><div className="bd">
                <div style={{ fontWeight: 700, fontSize: 17 }}>{p.name}</div>
                <div style={{ fontSize: 26, fontWeight: 700, margin: "6px 0" }}>${p.price_usd}<span style={{ fontSize: 13, color: "var(--muted)", fontWeight: 400 }}>/mo</span></div>
                <div style={{ color: "var(--muted)", fontSize: 13 }}>{p.tagline}</div>
              </div></div>
            ))}
          </div>
          <div style={{ textAlign: "center", marginTop: 18 }}>
            <a className="btn" href="/pricing">See full pricing</a>
          </div>
        </section>

        <section className="finalcta">
          <h2>Describe the outcome. Karya does the work.</h2>
          <a className="btn" href={cta}>{user ? "Open your workspace" : "Start free"}</a>
          <div className="foot">Karya · an AI workforce, behind one trust gate</div>
        </section>
      </div>
    </div>
  );
}
