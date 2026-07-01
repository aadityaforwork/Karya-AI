"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { CandidateDetail, TalentItem } from "../../lib/types";

export default function TalentPage() {
  const [talent, setTalent] = useState<TalentItem[] | null>(null);
  const [selected, setSelected] = useState<CandidateDetail | null>(null);

  useEffect(() => {
    api.talent().then((r) => setTalent(r.talent)).catch(() => setTalent([]));
  }, []);

  const open = (id: string) => api.candidate(id).then(setSelected).catch(() => {});

  return (
    <div className="page">
      <div className="lead">
        <h1>Talent pool</h1>
        <p>The seeded candidate pool the workers source from. Each résumé is stored as numbered lines, the exact evidence a screening claim must cite to be believed.</p>
      </div>

      {talent === null && <div className="empty">Loading…</div>}

      <div className="talent">
        {(talent || []).map((c) => (
          <div className="tcard" key={c.id} onClick={() => open(c.id)}>
            <div className="tn">{c.name} <span className="badge slate mono">{c.language}</span></div>
            <div className="th">{c.headline} · {c.location} · {c.years_experience}y</div>
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
              <div className="k">résumé · line-level evidence</div>
              <h2>{selected.name} <span className="badge slate mono">{selected.language}</span></h2>
              <div className="cost-sub" style={{ marginTop: 4 }}>{selected.headline} · {selected.location} · {selected.years_experience} years</div>
            </div>
            <div style={{ padding: "14px 19px" }}>
              <div className="sk" style={{ marginBottom: 12 }}>
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
            <div className="acts" style={{ padding: "8px 19px 19px" }}>
              <button className="btn ghost" onClick={() => setSelected(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
