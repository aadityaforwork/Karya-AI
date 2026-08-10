const PLANES = [
  { name: "Interface", color: "var(--sky)", desc: "Where you state the goal, watch the live feed, and approve what matters.", parts: ["Goal input", "Activity feed", "Approval queue"] },
  { name: "Orchestration", color: "var(--teal)", desc: "Breaks the goal into a plan, validates it as a DAG, schedules it, and self-heals on failure.", parts: ["Planner", "DAG validator", "Scheduler", "Reflector"] },
  { name: "Execution", color: "var(--mint)", desc: "Specialist workers run each step behind one cost-aware, language-aware model router.", parts: ["Router (tier 0→2)", "Sourcing", "Screening", "Outreach", "Tool sandbox"] },
  { name: "Trust", color: "var(--amber)", desc: "Nothing reaches you or the record unproven. Claims are grounded, risky actions gated, sends de-duplicated.", parts: ["Verifier", "Policy engine", "Idempotency guard"] },
  { name: "State", color: "var(--slate)", desc: "The append-only truth: every event, every citable line of evidence, every entity.", parts: ["Event log", "Evidence store", "Entity store"] },
];

const RULES = [
  { h: "Cheapest model that can be trusted", p: "Start cheap, escalate to a smarter model only when confidence is below the gate. You pay expert prices for the hard parts only." },
  { h: "No answer without proof", p: "Every claim must cite exact résumé lines. The verifier rejects anything not entailed by the evidence before it is ever saved or shown." },
  { h: "A human approves what matters", p: "The boring 95% runs on its own. Anything with real consequences, an external send, waits for your one-tap approval." },
];

const LANGS = [
  { l: "English", acc: "88%", to: "Cheap (tier 0)", badge: "mint" },
  { l: "Hindi", acc: "72%", to: "Cheap, watched", badge: "amber" },
  { l: "Marathi / Telugu", acc: "40%", to: "Starts smart (tier 1+)", badge: "rose" },
];

export default function HowItWorksPage() {
  return (
    <div className="page">
      <div className="lead">
        <h1>How Karya works</h1>
        <p>Five planes, each talking only to the one below it. Nothing reaches the record except through the trust plane.</p>
      </div>

      <div className="planes">
        {PLANES.map((pl) => (
          <div className="plane" key={pl.name} style={{ borderLeftColor: pl.color }}>
            <h4>{pl.name} plane</h4>
            <p>{pl.desc}</p>
            <div className="parts">
              {pl.parts.map((part) => <span className="tag mono" key={part}>{part}</span>)}
            </div>
          </div>
        ))}
      </div>

      <h3 className="subhead">Three rules make it work</h3>
      <div className="rules">
        {RULES.map((r, i) => (
          <div className="card" key={i}>
            <div className="bd">
              <div className="t">{r.h}</div>
              <div className="d">{r.p}</div>
            </div>
          </div>
        ))}
      </div>

      <h3 className="subhead spaced">We route by language, not just difficulty</h3>
      <div className="card">
        <div className="bd">
          <table className="langtable">
            <thead>
              <tr><th>Language</th><th>Cheap-model accuracy</th><th>Routed to</th></tr>
            </thead>
            <tbody>
              {LANGS.map((row) => (
                <tr key={row.l}>
                  <td>{row.l}</td>
                  <td><span className={`badge ${row.badge}`}>{row.acc}</span></td>
                  <td className="mono">{row.to}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="note langnote">
            Cheap models are strong in English and weak in Indian languages, so Karya starts low-accuracy languages on a smarter tier instead of wasting a doomed cheap call. These scores are learned from the verifier’s own outcomes over time.
          </p>
        </div>
      </div>
    </div>
  );
}
