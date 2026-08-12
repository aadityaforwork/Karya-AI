"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "../../lib/api";
import type { PoolFacets, Role } from "../../lib/types";
import { statusBadge } from "../../lib/ui";
import { SKILL_ACCENT, useSkills } from "../../lib/useSkills";

const join = (s: string[]) => s.join(", ");
const split = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

export default function WorkspacesPage() {
  const skills = useSkills();
  const skillList = useMemo(() => Object.values(skills).filter((s) => s.active), [skills]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [filter, setFilter] = useState("all");
  const [open, setOpen] = useState(false);
  const [skillId, setSkillId] = useState("hiring");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [facets, setFacets] = useState<PoolFacets | null>(null);
  const [form, setForm] = useState({ title: "", location: "", headcount: 2, must_have: "", nice_to_have: "", seniority: "" });

  const load = () => api.roles().then((r) => setRoles(r.roles)).catch(() => {});
  useEffect(() => { load(); }, []);

  // arrive from a skill card: /roles?skill=sales
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("skill");
    if (q) { setFilter(q); setSkillId(q); }
  }, []);

  // load defaults whenever the chosen skill changes
  useEffect(() => {
    const s = skills[skillId];
    if (s?.default_spec) {
      const d = s.default_spec;
      setForm({
        title: d.title || "", location: d.location || "", headcount: d.headcount || 1,
        must_have: join(d.must_have || []), nice_to_have: join(d.nice_to_have || []), seniority: d.seniority || "mid",
      });
    }
  }, [skillId, skills]);

  const cur = skills[skillId];
  const isSales = cur?.spec === "campaign";

  // What the chosen skill's pool actually holds. Without this the form invites
  // specs the pool can never match, and the workspace comes back empty.
  useEffect(() => {
    const pool = cur?.pool;
    if (!open || !pool) return;
    api.poolFacets(pool).then(setFacets).catch(() => setFacets(null));
  }, [open, cur?.pool]);

  const toggleSkill = (field: "must_have" | "nice_to_have", name: string) =>
    setForm((f) => {
      const cur = split(f[field]);
      const next = cur.includes(name) ? cur.filter((s) => s !== name) : [...cur, name];
      return { ...f, [field]: join(next) };
    });

  const unmatched = useMemo(() => {
    if (!facets) return [];
    const have = new Set(facets.skills.map((s) => s.name.toLowerCase()));
    return split(form.must_have).filter((s) => !have.has(s.toLowerCase()));
  }, [facets, form.must_have]);
  const create = async () => {
    setBusy(true);
    setErr("");
    try {
      await api.createRole({
        skill: skillId, title: form.title.trim(), location: form.location.trim(),
        headcount: Number(form.headcount) || 1, must_have: split(form.must_have),
        nice_to_have: split(form.nice_to_have), seniority: form.seniority.trim(),
      });
      setOpen(false); load();
    } catch (e: any) {
      setErr(e?.message || "Could not create workspace.");
    }
    setBusy(false);
  };
  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }));

  const shown = roles.filter((r) => filter === "all" || r.skill === filter);

  return (
    <div className="page">
      <div className="toolbar">
        <div className="lead compact">
          <h1>Workspaces</h1>
          <p>Each workspace is one skill working one goal, with its own pipeline.</p>
        </div>
        <button className="btn" onClick={() => setOpen((o) => !o)}>{open ? "Cancel" : "+ New workspace"}</button>
      </div>

      <div className="chips filterrow">
        <span className={`chip${filter === "all" ? " on" : ""}`} onClick={() => setFilter("all")}>All</span>
        {skillList.map((s) => (
          <span key={s.id} className={`chip${filter === s.id ? " on" : ""}`} onClick={() => setFilter(s.id)}>{s.name}</span>
        ))}
      </div>

      {open && (
        <div className="card createcard">
          <div className="bd">
            <div className="skillfield">
              <label className="fieldlabel">Skill</label>
              <div className="stagepick skillpick">
                {skillList.map((s) => (
                  <button key={s.id} className={skillId === s.id ? "on" : ""} onClick={() => setSkillId(s.id)}>{s.name}</button>
                ))}
              </div>
            </div>
            <div className="form">
              <div className="two">
                <div><label>{isSales ? "ICP / persona" : "Role title"}</label><input value={form.title} onChange={(e) => set("title", e.target.value)} /></div>
                <div><label>{isSales ? "Prospects" : "Headcount"}</label><input type="number" min={1} value={form.headcount} onChange={(e) => set("headcount", e.target.value)} /></div>
              </div>
              <div>
                <label>{isSales ? "Region" : "Location"}</label>
                <input value={form.location} onChange={(e) => set("location", e.target.value)} />
                {facets && facets.locations.length > 0 && (
                  <div className="chips hintrow">
                    {facets.locations.map((l) => (
                      <span
                        key={l.name}
                        className={`chip${form.location.trim().toLowerCase() === l.name.toLowerCase() ? " on" : ""}`}
                        onClick={() => set("location", l.name)}
                      >
                        {l.name} <span className="mono">{l.count}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label>{isSales ? "Required signals" : "Must-have skills"} (comma-separated)</label>
                <input value={form.must_have} onChange={(e) => set("must_have", e.target.value)} />
                {facets && (
                  <div className="chips hintrow">
                    {facets.skills.slice(0, 16).map((s) => (
                      <span
                        key={s.name}
                        className={`chip${split(form.must_have).some((x) => x.toLowerCase() === s.name.toLowerCase()) ? " on" : ""}`}
                        onClick={() => toggleSkill("must_have", s.name)}
                      >
                        {s.name} <span className="mono">{s.count}</span>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div><label>{isSales ? "Nice-to-have signals" : "Nice-to-have skills"}</label><input value={form.nice_to_have} onChange={(e) => set("nice_to_have", e.target.value)} /></div>

              {facets && unmatched.length > 0 && (
                <div className="autherr">
                  Nobody in the {facets.pool} pool ({facets.size} profiles) has{" "}
                  <b>{unmatched.join(", ")}</b>. This workspace will source nobody — pick from the
                  skills above, or <a href={`/talent?pool=${facets.pool}`} className="strong-ink">browse the pool →</a>
                </div>
              )}

              {err && <div className="autherr">{err} <a href="/billing" className="strong-ink">Upgrade →</a></div>}
              <div><button className="btn" disabled={busy || !form.title.trim()} onClick={create}>{busy ? "Creating…" : `Create ${cur?.spec || "workspace"}`}</button></div>
            </div>
          </div>
        </div>
      )}

      {shown.length === 0 && !open && <div className="empty">No workspaces here yet.</div>}

      <div className="rolegrid">
        {shown.map((r) => {
          const accent = SKILL_ACCENT[skills[r.skill]?.accent] || "var(--ink)";
          return (
            <a className="rolecard" href={`/roles/${r.id}`} key={r.id} style={{ borderLeft: `4px solid ${accent}` }}>
              <div className="rh">
                <div>
                  <div className="rt">{r.title}</div>
                  <div className="rm">{skills[r.skill]?.name || r.skill} · {r.location} · {r.headcount} target</div>
                </div>
                <span className={`badge ${statusBadge(r.status)}`}>{r.status}</span>
              </div>
              <div className="sk tagrow">
                {r.must_have.map((s) => <span className="tag mono" key={s}>{s}</span>)}
              </div>
              <div className="rs">
                <span><b>{r.pipeline_count || 0}</b> in pipeline</span>
                <span><b>{r.contacted || 0}</b> contacted</span>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
