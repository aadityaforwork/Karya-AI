"use client";

import { useEffect, useState } from "react";
import ActivityFeed from "../../components/console/ActivityFeed";
import ApprovalModal from "../../components/console/ApprovalModal";
import Candidates from "../../components/console/Candidates";
import CostMeter from "../../components/console/CostMeter";
import Pipeline from "../../components/console/Pipeline";
import Report from "../../components/console/Report";
import { api } from "../../lib/api";
import type { RunCandidate } from "../../lib/types";
import { useKarya } from "../../lib/useKarya";

const EXAMPLES = [
  "Hire 2 backend engineers in Pune",
  "Hire 1 senior backend engineer in Bangalore",
  "Hire 3 full-stack engineers in Mumbai",
];

export default function PlaygroundPage() {
  const { events, runId, derived, startGoal, approve } = useKarya();
  const [text, setText] = useState("");
  const [rich, setRich] = useState<RunCandidate[]>([]);

  const running = derived.status === "running" || derived.status === "awaiting_approval";

  useEffect(() => {
    if (derived.report && runId) {
      api.runCandidates(runId).then((r) => setRich(r.candidates)).catch(() => {});
    }
  }, [derived.report, runId]);

  const submit = () => {
    const t = text.trim();
    if (t) { setRich([]); startGoal(t); }
  };

  return (
    <div className="page">
      <div className="lead">
        <h1>Playground</h1>
        <p>Run any goal ad-hoc and watch the engine work in real time: the planner, the cost-aware router, the evidence checks, the approval gate. (Roles and pipeline live under Workspaces.)</p>
      </div>

      <div className="goalbar">
        <input
          value={text}
          placeholder="e.g. Hire 2 backend engineers in Pune"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button className="btn" onClick={submit} disabled={running || !text.trim()}>
          {running ? "Running…" : "Run goal"}
        </button>
      </div>
      <div className="chips">
        {EXAMPLES.map((ex) => (
          <span key={ex} className="chip" onClick={() => { setText(ex); setRich([]); startGoal(ex); }}>{ex}</span>
        ))}
      </div>

      {derived.nodes.length > 0 && <div className="section-gap"><Pipeline nodes={derived.nodes} /></div>}

      <div className="cols">
        <ActivityFeed events={events} />
        <div className="stack">
          <CostMeter cost={derived.cost} comparison={derived.report?.cost_comparison} />
          <Candidates rich={rich} screened={derived.screened} />
        </div>
      </div>

      {derived.report && <div className="section-gap"><Report report={derived.report} /></div>}
      {derived.pendingApproval && <ApprovalModal approval={derived.pendingApproval} onDecide={approve} />}
    </div>
  );
}
