"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import ApprovalModal from "../../../components/console/ApprovalModal";
import CandidateDrawer from "../../../components/product/CandidateDrawer";
import { api } from "../../../lib/api";
import { FUNNEL, type ApprovalQueueItem, type PipelineCandidate, type Role, type Stage } from "../../../lib/types";
import { SKILL_ACCENT, stageLabel, useSkills } from "../../../lib/useSkills";

const COLUMNS: Stage[] = [...FUNNEL, "rejected"];
const COLOR: Record<string, string> = {
  sourced: "var(--slate)", screened: "var(--sky)", contacted: "var(--teal)",
  replied: "var(--mint)", interview: "var(--amber)", offer: "var(--mint)", rejected: "var(--rose)",
};

export default function RoleDetailPage() {
  const id = String(useParams().id);
  const skills = useSkills();
  const [role, setRole] = useState<Role | null>(null);
  const [pipe, setPipe] = useState<PipelineCandidate[]>([]);
  const [selected, setSelected] = useState<PipelineCandidate | null>(null);
  const [approval, setApproval] = useState<ApprovalQueueItem | null>(null);
  const [running, setRunning] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const refresh = useCallback(() => {
    api.rolePipeline(id).then((r) => setPipe(r.pipeline)).catch(() => {});
    api.approvalsQueue().then((r) => setApproval(r.approvals.find((a) => a.role_id === id) || null)).catch(() => {});
  }, [id]);

  useEffect(() => {
    api.role(id).then((r) => setRole(r.role)).catch(() => setNotFound(true));
    refresh();
    const t = setInterval(refresh, 2500);
    return () => clearInterval(t);
  }, [id, refresh]);

  useEffect(() => {
    if (selected) {
      const u = pipe.find((p) => p.id === selected.id);
      if (u && u.stage !== selected.stage) setSelected(u);
    }
  }, [pipe]); // eslint-disable-line react-hooks/exhaustive-deps

  const run = async () => {
    setRunning(true);
    await api.runRole(id);
    setTimeout(() => setRunning(false), 4000);
    refresh();
  };

  const byStage = useMemo(() => {
    const m: Record<string, PipelineCandidate[]> = {};
    for (const s of COLUMNS) m[s] = [];
    for (const p of pipe) (m[p.stage] ||= []).push(p);
    return m;
  }, [pipe]);

  if (notFound) {
    return (
      <div className="page">
        <div className="empty">
          Workspace not found. It may have been removed, or belongs to another account.{" "}
          <a href="/roles" className="strong-ink">Back to workspaces →</a>
        </div>
      </div>
    );
  }
  if (!role) return <div className="page"><div className="empty">Loading…</div></div>;
  const skill = skills[role.skill];
  const accent = SKILL_ACCENT[skill?.accent] || "var(--ink)";
  const noun = skill?.entity_plural || "candidates";

  return (
    <div className="page">
      <div className="toolbar">
        <div className="lead compact">
          <h1 className="roletitle">
            <span className="dot lg" style={{ background: accent }} />
            {role.title} <span className="roleloc">· {role.location}</span>
          </h1>
          <p>
            <span className="badge chipbg">{skill?.name || role.skill}</span>
            {" "}· {role.headcount} target · {role.must_have.join(", ")} · <a href="/roles" className="muted">all workspaces</a>
          </p>
        </div>
        <button className="btn" onClick={run} disabled={running}>{running ? "Working…" : "Run sourcing"}</button>
      </div>

      {approval && (
        <div className="card approvalbanner">
          <div className="bd row-mid">
            <span><b>Approval waiting</b> · {approval.summary}</span>
            <span className="badge amber">review below</span>
          </div>
        </div>
      )}

      {pipe.length === 0 ? (
        <div className="empty">No {noun} yet. Hit “Run sourcing” and Karya sources, qualifies with evidence, drafts outreach, then asks you to approve the send.</div>
      ) : (
        <div className="board">
          {COLUMNS.map((s) => (
            <div className="col" key={s}>
              <div className="ch"><span style={{ color: COLOR[s] }}>{stageLabel(skill, s)}</span><span className="cn">{byStage[s].length}</span></div>
              {byStage[s].map((p) => (
                <div className="pcard" key={p.id} onClick={() => setSelected(p)}>
                  <div className="pn"><span>{p.name}</span><span className="mono">{Math.round(p.fit * 100)}%</span></div>
                  <div className="pm">{p.language} · {p.claims.filter((c) => c.status === "verified").length} proven</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {selected && <CandidateDrawer pc={selected} skill={skill} onClose={() => setSelected(null)} onChanged={refresh} />}
      {approval && <ApprovalModal approval={{ approval_id: approval.id, summary: approval.summary, drafts: approval.payload.drafts }} onDecide={async (aid, d) => { await api.approve(aid, d); setApproval(null); setTimeout(refresh, 800); }} />}
    </div>
  );
}
