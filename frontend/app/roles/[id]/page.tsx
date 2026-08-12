"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import ActivityFeed from "../../../components/console/ActivityFeed";
import ApprovalModal from "../../../components/console/ApprovalModal";
import CostMeter from "../../../components/console/CostMeter";
import Pipeline from "../../../components/console/Pipeline";
import CandidateDrawer from "../../../components/product/CandidateDrawer";
import { ApiError, api } from "../../../lib/api";
import { FUNNEL, type NoMatch, type PipelineCandidate, type Role, type Stage } from "../../../lib/types";
import { SKILL_ACCENT, stageLabel, useSkills } from "../../../lib/useSkills";
import { useKarya } from "../../../lib/useKarya";

const COLUMNS: Stage[] = [...FUNNEL, "rejected"];
const COLOR: Record<string, string> = {
  sourced: "var(--slate)", screened: "var(--sky)", contacted: "var(--teal)",
  replied: "var(--mint)", interview: "var(--amber)", offer: "var(--mint)", rejected: "var(--rose)",
};

// What the run is doing right now, in the user's words rather than the engine's.
const PHASE: Record<string, string> = {
  running: "Working…",
  awaiting_approval: "Waiting on you",
  done: "Run sourcing",
  failed: "Run sourcing",
  idle: "Run sourcing",
};

export default function RoleDetailPage() {
  const id = String(useParams().id);
  const skills = useSkills();
  const { events, runId, derived, attach, approve } = useKarya();
  const [role, setRole] = useState<Role | null>(null);
  const [pipe, setPipe] = useState<PipelineCandidate[]>([]);
  const [selected, setSelected] = useState<PipelineCandidate | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const live = derived.status === "running" || derived.status === "awaiting_approval";
  const busy = starting || live;
  const noMatch = (derived.report?.no_match as NoMatch | null | undefined) || null;

  const refresh = useCallback(() => {
    api.rolePipeline(id).then((r) => setPipe(r.pipeline)).catch(() => {});
  }, [id]);

  // On mount, rejoin a run that is still in flight so a reload never strands the
  // user on a board that looks idle while work is happening.
  useEffect(() => {
    api.role(id)
      .then((r) => {
        setRole(r.role);
        if (r.active_run) attach(r.active_run);
      })
      .catch(() => setNotFound(true));
    refresh();
  }, [id, refresh, attach]);

  // The board is durable state, written only once a run finishes. Poll it while
  // a run is live (cheap, and it catches the moment results land), and pull it
  // once more on completion.
  useEffect(() => {
    if (!live) return;
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [live, refresh]);

  useEffect(() => {
    if (derived.status === "done" || derived.status === "failed") {
      refresh();
      const t = setTimeout(refresh, 1200);
      return () => clearTimeout(t);
    }
  }, [derived.status, refresh]);

  useEffect(() => {
    if (!selected) return;
    const u = pipe.find((p) => p.id === selected.id);
    if (u && u.stage !== selected.stage) setSelected(u);
  }, [pipe]); // eslint-disable-line react-hooks/exhaustive-deps

  const run = async () => {
    setError(null);
    setStarting(true);
    try {
      const { run_id } = await api.runRole(id);
      attach(run_id);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 402
          ? `${e.message}. Upgrade on the billing page to keep running.`
          : "Could not start the run. Check the backend is running and try again.",
      );
    } finally {
      setStarting(false);
    }
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
        <button className="btn" onClick={run} disabled={busy}>
          {starting ? "Starting…" : PHASE[derived.status] || "Run sourcing"}
        </button>
      </div>

      {error && <div className="card approvalbanner"><div className="bd">{error}</div></div>}

      {/* The run, as it happens. Sourcing and screening used to be invisible
          here: the board stayed empty until everything finished, and the
          approval appeared out of nowhere. */}
      {runId && events.length > 0 && (
        <div className="section-gap">
          <Pipeline nodes={derived.nodes} />
          <div className="cols">
            <ActivityFeed events={events} />
            <div className="stack">
              <CostMeter cost={derived.cost} comparison={derived.report?.cost_comparison} />
              {derived.screened.length > 0 && (
                <div className="card">
                  <div className="hd">
                    <h3>Screened so far</h3>
                    <span className="badge slate mono">{derived.screened.length}</span>
                  </div>
                  <div className="bd">
                    {derived.screened.map((s) => (
                      <div className="screenrow" key={s.candidate_id}>
                        <span className="nm">{s.name} <span className="badge slate mono">{s.language}</span></span>
                        <span className="mono st">
                          {Math.round(s.fit * 100)}% · {s.verified.length} proven
                          {s.rejected.length > 0 && <> · {s.rejected.length} bounced</>}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {derived.status === "awaiting_approval" && (
        <div className="card approvalbanner">
          <div className="bd row-mid">
            <span><b>Approval waiting</b> · {derived.pendingApproval?.summary}</span>
            <span className="badge amber">review below</span>
          </div>
        </div>
      )}

      {/* A run that matched nobody used to look identical to one never started.
          Say what the pool holds so the spec can be fixed. */}
      {noMatch && (
        <div className="card approvalbanner">
          <div className="bd">
            <b>Nothing in the {noMatch.pool} pool matches this workspace.</b>
            <div className="mt8">
              None of the {noMatch.pool_size} profiles has{" "}
              <b>{noMatch.requested.join(", ") || "these skills"}</b>. The pool is strongest on:
            </div>
            <div className="chips hintrow">
              {noMatch.available_skills.map((s) => <span className="chip" key={s}>{s}</span>)}
            </div>
            <div className="mt8">
              Edit the must-have skills from <a href="/roles" className="strong-ink">Workspaces</a>, or{" "}
              <a href={`/talent?pool=${noMatch.pool}`} className="strong-ink">browse the pool →</a>
            </div>
          </div>
        </div>
      )}

      {pipe.length === 0 ? (
        <div className="empty">
          {live
            ? `Working on it — ${noun} land on the board once the run finishes.`
            : noMatch
              ? `This run sourced no ${noun}. Adjust the spec above and run again.`
              : `No ${noun} yet. Hit “Run sourcing” and Karya sources, qualifies with evidence, drafts outreach, then asks you to approve the send.`}
        </div>
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
      {derived.pendingApproval && (
        <ApprovalModal
          approval={derived.pendingApproval}
          onDecide={async (aid, d) => {
            try {
              await approve(aid, d);
            } catch (e) {
              setError(e instanceof ApiError ? e.message : "Could not record that decision.");
            }
          }}
        />
      )}
    </div>
  );
}
