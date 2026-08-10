"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { FUNNEL, STAGE_LABEL, type Dashboard, type Role, type Skill } from "../../lib/types";
import { SKILL_ACCENT } from "../../lib/useSkills";
import { useAuth } from "../../lib/auth";

const STAGE_COLOR: Record<string, string> = {
  sourced: "var(--slate)", screened: "var(--sky)", contacted: "var(--teal)",
  replied: "var(--mint)", interview: "var(--amber)", offer: "var(--mint)",
};
const LANG_COLOR: Record<string, string> = { en: "var(--sky)", hi: "var(--amber)", mr: "var(--rose)", te: "var(--teal)" };
const TIER = { "0": "Tier 0 cheap", "1": "Tier 1 mid", "2": "Tier 2 top" } as Record<string, string>;
const TIER_C = { "0": "var(--mint)", "1": "var(--amber)", "2": "var(--sky)" } as Record<string, string>;

export default function AppHomePage() {
  const { user } = useAuth();
  const [d, setD] = useState<Dashboard | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);

  useEffect(() => {
    api.dashboard().then(setD).catch(() => {});
    api.roles().then((r) => setRoles(r.roles)).catch(() => {});
    api.skills().then((r) => setSkills(r.skills)).catch(() => {});
  }, []);

  const allowed = (s: Skill) => s.active && (user?.plan === "business" || (user?.plan === "pro" ? ["hiring", "sales"] : ["hiring"]).includes(s.id));

  return (
    <div className="page">
      <div className="lead">
        <h1>Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}.</h1>
        <p>Describe an outcome and a team of AI workers does the job, cheaply, with every claim grounded in evidence. Pick a skill to begin.</p>
      </div>

      <div className="rolegrid skillgrid">
        {skills.map((s) => {
          const stat = d?.by_skill?.[s.id];
          const accent = SKILL_ACCENT[s.accent] || "var(--ink)";
          const ok = allowed(s);
          return (
            <div className="rolecard" key={s.id} style={{ opacity: s.active ? 1 : 0.5 }}>
              <div className="rh">
                <div>
                  <div className="rt skillname">
                    <span className="dot" style={{ background: accent }} />
                    {s.name}
                  </div>
                  <div className="rm">{s.tagline}</div>
                </div>
                {s.active ? <span className="badge mint">live</span> : <span className="badge slate">soon</span>}
              </div>
              {s.active ? (
                <>
                  <div className="rs">
                    <span><b>{stat?.roles || 0}</b> {s.spec_plural}</span>
                    <span><b>{stat?.pipeline || 0}</b> {s.entity_plural}</span>
                    <span><b>{stat?.contacted || 0}</b> contacted</span>
                  </div>
                  {ok ? (
                    <a className="btn ghost skillcta" href={`/roles?skill=${s.id}`}>Open {s.name} <span aria-hidden>→</span></a>
                  ) : (
                    <a className="btn ghost skillcta upgrade" href="/billing">Upgrade to unlock <span aria-hidden>→</span></a>
                  )}
                </>
              ) : (
                <div className="rs"><span className="faint">Same engine, coming next.</span></div>
              )}
            </div>
          );
        })}
      </div>

      {d && (
        <>
          <div className="statgrid">
            <div className="stat hero">
              <div className="v">${d.cost.saved_usd}</div>
              <div className="l">saved vs frontier-only</div>
              <div className="sub">{d.cost.savings_x ? `≈${d.cost.savings_x}× cheaper` : "run a workspace to see savings"}</div>
            </div>
            <div className="stat"><div className="v">{d.hours_saved}h</div><div className="l">time saved</div><div className="sub">across all skills</div></div>
            <div className="stat"><div className="v">{d.pipeline.total}</div><div className="l">in pipeline</div><div className="sub">{d.outreach_sent} outreach sent</div></div>
            <div className="stat"><div className="v claimsplit"><span className="ok">{d.claims.verified}</span><span className="sep"> / </span><span className="no">{d.claims.rejected}</span></div><div className="l">claims proven / rejected</div><div className="sub">never trust without proof</div></div>
          </div>

          <div className="split">
            <div className="card">
              <div className="hd"><h3>Pipeline funnel</h3></div>
              <div className="bd">
                {d.pipeline.total === 0 ? <div className="empty">No candidates yet.</div> : (
                  <div className="funnel">
                    {FUNNEL.map((s) => {
                      const n = d.pipeline.funnel[s] || 0;
                      const mx = Math.max(1, ...FUNNEL.map((x) => d.pipeline.funnel[x] || 0));
                      return (
                        <div className="frow" key={s}>
                          <span>{STAGE_LABEL[s]}</span>
                          <div className="ftrack"><div className="ffill" style={{ width: `${(n / mx) * 100}%`, background: STAGE_COLOR[s] }} /></div>
                          <span>{n}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            <div className="card">
              <div className="hd"><h3>Where the spend goes</h3></div>
              <div className="bd">
                <div className="kicker">Model-tier calls</div>
                {["0", "1", "2"].map((t) => {
                  const mx = Math.max(1, ...Object.values(d.tier_calls).map(Number));
                  return (
                    <div className="barline" key={t}>
                      <span className="lbl">{TIER[t]}</span>
                      <div className="track"><div className="fill" style={{ width: `${((Number(d.tier_calls[t]) || 0) / mx) * 100}%`, background: TIER_C[t] }} /></div>
                      <span className="mono barcount">{d.tier_calls[t] || 0}</span>
                    </div>
                  );
                })}
                <div className="kicker spaced">Subjects by language</div>
                {Object.entries(d.language_mix).map(([l, n]) => {
                  const mx = Math.max(1, ...Object.values(d.language_mix));
                  return (
                    <div className="barline" key={l}>
                      <span className="lbl mono">{l}</span>
                      <div className="track"><div className="fill" style={{ width: `${(n / mx) * 100}%`, background: LANG_COLOR[l] || "var(--slate)" }} /></div>
                      <span className="mono barcount">{n}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}

      {roles.length > 0 && (
        <div className="card recentcard">
          <div className="hd"><h3>Recent workspaces</h3><a className="btn ghost recentall" href="/roles">All <span aria-hidden>→</span></a></div>
          <div className="bd">
            {roles.slice(0, 5).map((r) => (
              <a className="minirow" href={`/roles/${r.id}`} key={r.id}>
                <span><b>{r.title}</b> · {r.location}</span>
                <span className="mono muted">{r.skill} · {r.pipeline_count || 0} in pipeline</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
