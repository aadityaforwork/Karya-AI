"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "../../lib/api";
import type { Role } from "../../lib/types";
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
        <div className="lead" style={{ margin: 0 }}>
          <h1>Workspaces</h1>
          <p style={{ marginTop: 4 }}>Each workspace is one skill working one goal, with its own pipeline.</p>
        </div>
        <button className="btn" onClick={() => setOpen((o) => !o)}>{open ? "Cancel" : "+ New workspace"}</button>
      </div>

      <div className="chips" style={{ marginBottom: 16 }}>
        <span className={`chip ${filter === "all" ? "" : ""}`} style={filter === "all" ? { borderColor: "var(--ink)", color: "var(--ink)" } : {}} onClick={() => setFilter("all")}>All</span>
        {skillList.map((s) => (
          <span key={s.id} className="chip" style={filter === s.id ? { borderColor: "var(--ink)", color: "var(--ink)" } : {}} onClick={() => setFilter(s.id)}>{s.name}</span>
        ))}
      </div>

      {open && (
        <div className="card" style={{ marginBottom: 18 }}>
          <div className="bd">
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 12, color: "var(--muted)", fontWeight: 600 }}>Skill</label>
              <div className="stagepick" style={{ marginTop: 6 }}>
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
              <div><label>{isSales ? "Region" : "Location"}</label><input value={form.location} onChange={(e) => set("location", e.target.value)} /></div>
              <div><label>{isSales ? "Required signals" : "Must-have skills"} (comma-separated)</label><input value={form.must_have} onChange={(e) => set("must_have", e.target.value)} /></div>
              <div><label>{isSales ? "Nice-to-have signals" : "Nice-to-have skills"}</label><input value={form.nice_to_have} onChange={(e) => set("nice_to_have", e.target.value)} /></div>
              {err && <div className="autherr">{err} <a href="/billing" style={{ color: "var(--ink)", fontWeight: 600 }}>Upgrade →</a></div>}
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
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div className="rt">{r.title}</div>
                  <div className="rm">{skills[r.skill]?.name || r.skill} · {r.location} · {r.headcount} target</div>
                </div>
                <span className={`badge ${statusBadge(r.status)}`}>{r.status}</span>
              </div>
              <div className="sk" style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
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
