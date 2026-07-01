"use client";

import { useState } from "react";
import type { PendingApproval } from "../../lib/types";
import { Check } from "../icons";

export default function ApprovalModal({
  approval,
  onDecide,
}: {
  approval: PendingApproval;
  onDecide: (id: string, decision: boolean) => Promise<void> | void;
}) {
  const [busy, setBusy] = useState(false);
  const decide = async (d: boolean) => {
    setBusy(true);
    await onDecide(approval.approval_id, d);
  };

  return (
    <div className="overlay">
      <div className="modal">
        <div className="mh">
          <div className="k">Approval needed · one tap</div>
          <h2>{approval.summary}</h2>
        </div>
        {approval.drafts.map((d) => (
          <div className="draft" key={d.candidate_id}>
            <div className="sj">
              {d.subject} <span className="badge slate mono">{d.language}</span>
            </div>
            <div className="bd2">{d.body}</div>
            {d.cited_facts.length > 0 && <div className="ct"><Check size={13} /> cites: {d.cited_facts.join(" · ")}</div>}
          </div>
        ))}
        <div className="acts">
          <button className="btn" style={{ flex: 1 }} disabled={busy} onClick={() => decide(true)}>
            Approve &amp; send
          </button>
          <button className="btn ghost" style={{ flex: 1 }} disabled={busy} onClick={() => decide(false)}>
            Decline
          </button>
        </div>
      </div>
    </div>
  );
}
