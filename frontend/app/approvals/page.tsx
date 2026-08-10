"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { ApprovalQueueItem } from "../../lib/types";
import { Check } from "../../components/icons";

export default function ApprovalsPage() {
  const [items, setItems] = useState<ApprovalQueueItem[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(() => api.approvalsQueue().then((r) => setItems(r.approvals)).catch(() => {}), []);
  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [load]);

  const decide = async (id: string, decision: boolean) => {
    setBusy(id);
    await api.approve(id, decision);
    setItems((xs) => xs.filter((x) => x.id !== id));
    setBusy(null);
  };

  return (
    <div className="page">
      <div className="lead">
        <h1>Approvals</h1>
        <p>Karya does the boring 95% on its own. Anything that leaves the system, an external send, waits here for your one-tap approval.</p>
      </div>

      {items.length === 0 && <div className="empty">Nothing waiting. When a run is ready to send outreach, it shows up here.</div>}

      {items.map((a) => (
        <div className="aqcard" key={a.id}>
          <div className="ah">
            <div>
              <div className="ag">{a.role_title || "Ad-hoc run"}</div>
              <div className="am">{a.goal} · {a.summary}</div>
            </div>
            <span className="badge amber">risk tier {a.risk_tier}</span>
          </div>
          {a.payload.drafts.map((d) => (
            <div className="draft stacked" key={d.candidate_id}>
              <div className="sj">{d.subject} <span className="badge slate mono">{d.language}</span></div>
              <div className="bd2">{d.body}</div>
              {d.cited_facts.length > 0 && <div className="ct"><Check size={13} /> cites: {d.cited_facts.join(" · ")}</div>}
            </div>
          ))}
          <div className="acts aqacts">
            <button className="btn" disabled={busy === a.id} onClick={() => decide(a.id, true)}>Approve &amp; send</button>
            <button className="btn ghost" disabled={busy === a.id} onClick={() => decide(a.id, false)}>Decline</button>
          </div>
        </div>
      ))}
    </div>
  );
}
