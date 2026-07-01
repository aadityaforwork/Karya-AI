"use client";

import { Check } from "../icons";

export default function Report({ report }: { report: Record<string, any> }) {
  const claims = report.claims || {};
  const cmp = report.cost_comparison || {};
  return (
    <div className="card">
      <div className="hd"><h3>Run report</h3></div>
      <div className="bd">
        <div className="kpis">
          <div className="kpi"><div className="v">{report.sourced ?? 0}</div><div className="l">sourced</div></div>
          <div className="kpi"><div className="v">{report.sent ?? 0}</div><div className="l">outreach sent</div></div>
          <div className="kpi"><div className="v" style={{ color: "var(--mint)" }}>{claims.verified ?? 0}</div><div className="l">claims proven</div></div>
          <div className="kpi"><div className="v" style={{ color: "var(--rose)" }}>{claims.rejected ?? 0}</div><div className="l">claims rejected</div></div>
        </div>

        <div style={{ marginTop: 16, fontWeight: 600 }}>Finalists</div>
        {(report.finalists || []).map((f: any) => (
          <div className="cand" key={f.name} style={{ marginTop: 8 }}>
            <div className="row" style={{ cursor: "default" }}>
              <div>
                <div className="nm">{f.name}<span className="badge slate mono" style={{ marginLeft: 6 }}>{f.language}</span></div>
                <div className="meta">{(f.proven_facts || []).length} cited facts</div>
              </div>
              <span className="fit advance">{Math.round((f.fit || 0) * 100)}%</span>
            </div>
            {(f.proven_facts || []).length > 0 && (
              <div className="detail">
                {(f.proven_facts || []).map((p: string, i: number) => (
                  <div key={i} className="claim ok"><span className="ic"><Check /></span><div>{p}</div></div>
                ))}
              </div>
            )}
          </div>
        ))}

        {cmp.savings_x != null && (
          <div className="compare" style={{ marginTop: 16 }}>
            <span className="x">≈{cmp.savings_x}× cheaper</span>
            <span className="cost-sub" style={{ marginLeft: 10 }}>
              ${cmp.karya_usd} on Karya vs ${cmp.frontier_only_usd} frontier-only
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
