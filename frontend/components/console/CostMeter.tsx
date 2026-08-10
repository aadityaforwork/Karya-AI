"use client";

import type { CostSnapshot } from "../../lib/types";

export default function CostMeter({ cost, comparison }: { cost: CostSnapshot; comparison?: any }) {
  const t = (i: string) => cost.by_tier[i] || 0;
  const c = (i: string) => cost.calls_by_tier[i] || 0;
  const total = cost.total_usd || 0;
  const pct = (v: number) => (total > 0 ? (v / total) * 100 : 0);
  const rows = [
    { i: "0", name: "Tier 0 · cheap", sw: "sw0" },
    { i: "1", name: "Tier 1 · mid", sw: "sw1" },
    { i: "2", name: "Tier 2 · frontier", sw: "sw2" },
  ];

  return (
    <div className="card">
      <div className="hd"><h3>Cost</h3></div>
      <div className="bd">
        <div className="cost-big mono">${total.toFixed(4)}</div>
        <div className="cost-sub">spent on this goal</div>
        <div className="tierbar">
          <span className="sw0" style={{ width: `${pct(t("0"))}%` }} />
          <span className="sw1" style={{ width: `${pct(t("1"))}%` }} />
          <span className="sw2" style={{ width: `${pct(t("2"))}%` }} />
        </div>
        {rows.map((r) => (
          <div className="trow" key={r.i}>
            <span className="k"><i className={`d ${r.sw}`} />{r.name}</span>
            <span className="mono">{c(r.i)} calls · ${t(r.i).toFixed(4)}</span>
          </div>
        ))}
        {comparison?.frontier_only_usd != null && (
          <div className="compare">
            <span className="x">≈{comparison.savings_x}× cheaper</span>
            <div className="cost-sub mt-tight">
              vs ${comparison.frontier_only_usd} running the frontier model for everything
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
