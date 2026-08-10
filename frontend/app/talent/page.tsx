"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { CandidateDetail, TalentItem } from "../../lib/types";
import { useSkills } from "../../lib/useSkills";

export default function TalentPage() {
  const skills = useSkills();
  const pools = Object.values(skills).filter((s) => s.active);
  const [pool, setPool] = useState("talent");
  const [talent, setTalent] = useState<TalentItem[] | null>(null);
  const [selected, setSelected] = useState<CandidateDetail | null>(null);

  // once skills load, default to whichever skill's pool matches the ?skill= query, if any
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("skill");
    const s = q && skills[q];
    if (s) setPool(s.pool);
  }, [skills]);

  useEffect(() => {
    setTalent(null);
    api.talent(pool).then((r) => setTalent(r.talent)).catch(() => setTalent([]));
  }, [pool]);

  const open = (id: string) => api.candidate(id).then(setSelected).catch(() => {});
  const activeSkill = pools.find((s) => s.pool === pool);

  return (
    <div className="page">
      <div className="lead">
        <h1>{activeSkill ? `${activeSkill.entity_plural[0].toUpperCase()}${activeSkill.entity_plural.slice(1)} pool` : "Talent pool"}</h1>
        <p>The seeded {activeSkill?.entity || "candidate"} pool the workers source from. Each profile is stored as numbered lines, the exact evidence a screening claim must cite to be believed.</p>
      </div>

      {pools.length > 1 && (
        <div className="chips filterrow">
          {pools.map((s) => (
            <span key={s.id} className={`chip${pool === s.pool ? " on" : ""}`} onClick={() => setPool(s.pool)}>{s.name}</span>
          ))}
        </div>
      )}

      {talent === null && <div className="empty">Loading…</div>}

      <div className="talent">
        {(talent || []).map((c) => (
          <div className="tcard" key={c.id} onClick={() => open(c.id)}>
            <div className="tn">{c.name} <span className="badge slate mono">{c.language}</span></div>
            <div className="th">{c.headline} · {c.location}{c.years_experience > 0 ? ` · ${c.years_experience}y` : ""}</div>
            <div className="sk">
              {c.skills.slice(0, 5).map((s) => <span className="tag mono" key={s}>{s}</span>)}
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <div className="overlay" onClick={() => setSelected(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="mh">
              <div className="k">{pool === "talent" ? "résumé" : "profile"} · line-level evidence</div>
              <h2>{selected.name} <span className="badge slate mono">{selected.language}</span></h2>
              <div className="cost-sub modaltight">{selected.headline} · {selected.location}{selected.years_experience > 0 ? ` · ${selected.years_experience} years` : ""}</div>
            </div>
            <div className="modalbody">
              <div className="sk tagrow tight">
                {selected.skills.map((s) => <span className="tag mono" key={s}>{s}</span>)}
              </div>
              <div className="resume">
                {selected.resume.map((l) => (
                  <div className="rline" key={l.n}>
                    <span className="n mono">L{l.n}</span>
                    <span>{l.text}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="acts modalacts">
              <button className="btn ghost" onClick={() => setSelected(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
