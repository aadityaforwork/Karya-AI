"use client";

import type { PlanNodeView } from "../../lib/types";

const LABEL: Record<string, string> = {
  SOURCE: "Source",
  SCREEN: "Screen + verify",
  DRAFT_OUTREACH: "Draft",
  SEND_OUTREACH: "Approve + send",
  REPORT: "Report",
};
const STATE: Record<string, string> = {
  pending: "queued",
  running: "running…",
  done: "done",
  failed: "failed",
};

export default function Pipeline({ nodes }: { nodes: PlanNodeView[] }) {
  if (nodes.length === 0) return null;
  return (
    <div className="card">
      <div className="hd"><h3>Plan</h3></div>
      <div className="bd">
        <div className="pipe">
          {nodes.map((n) => (
            <div key={n.id} className={`step ${n.status}`}>
              <div className="bar" />
              <div className="t">{LABEL[n.type] || n.type}</div>
              <div className="s">{STATE[n.status]}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
