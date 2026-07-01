"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Billing } from "../../lib/types";
import { Check } from "../../components/icons";

function Usage({ label, used, limit }: { label: string; used: number; limit: number }) {
  const unlimited = limit < 0;
  const pct = unlimited ? 8 : Math.min(100, (used / Math.max(1, limit)) * 100);
  return (
    <div className="barline" style={{ alignItems: "center" }}>
      <span className="lbl" style={{ width: 100 }}>{label}</span>
      <div className="track"><div className="fill" style={{ width: `${pct}%`, background: pct > 85 && !unlimited ? "var(--rose)" : "var(--mint)" }} /></div>
      <span className="mono" style={{ width: 72, textAlign: "right" }}>{used}{unlimited ? "" : ` / ${limit}`}</span>
    </div>
  );
}

export default function BillingPage() {
  const { refresh } = useAuth();
  const [b, setB] = useState<Billing | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(() => api.billing().then(setB).catch(() => {}), []);
  useEffect(() => { load(); }, [load]);

  const choose = async (plan: string) => {
    setBusy(plan);
    await api.subscribe(plan);
    await refresh();
    await load();
    setBusy(null);
  };

  if (!b) return <div className="page"><div className="empty">Loading billing…</div></div>;

  return (
    <div className="page">
      <div className="lead">
        <h1>Billing &amp; plan</h1>
        <p>You're on the <b style={{ color: "var(--ink)" }}>{b.plan}</b> plan. Switch any time. It takes effect instantly.</p>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <div className="hd"><h3>This cycle's usage</h3></div>
        <div className="bd">
          <Usage label="Workspaces" used={b.usage.workspaces} limit={b.usage.workspace_limit} />
          <Usage label="Runs" used={b.usage.runs} limit={b.usage.runs_limit} />
        </div>
      </div>

      <div className="plans">
        {b.plans.map((p) => {
          const current = p.id === b.plan;
          return (
            <div className={`plancard ${current ? "current" : p.id === "pro" ? "featured" : ""}`} key={p.id}>
              <div className="pname">{p.name}{current && <span className="badge mint" style={{ marginLeft: 6 }}>current</span>}</div>
              <div className="pprice">${p.price_usd}<span>/mo</span></div>
              <div className="ptag">{p.tagline}</div>
              <div style={{ margin: "14px 0" }}>
                {p.features.map((f) => <div className="feat" key={f}><span className="ic"><Check size={13} /></span>{f}</div>)}
              </div>
              <button className={`btn ${current ? "ghost" : ""}`} disabled={current || busy === p.id} onClick={() => choose(p.id)}>
                {current ? "Current plan" : busy === p.id ? "Switching…" : `Switch to ${p.name}`}
              </button>
            </div>
          );
        })}
      </div>

      <p style={{ textAlign: "center", color: "var(--faint)", fontSize: 12.5, marginTop: 20 }}>
        Checkout is mocked in this build. A real processor (Stripe) slots in behind the subscribe action.
      </p>
    </div>
  );
}
