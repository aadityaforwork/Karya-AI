"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { FUNNEL, type Message, type PipelineCandidate, type ReplyIntent, type ReplySuggestion, type Skill, type Stage } from "../../lib/types";
import { stageLabel } from "../../lib/useSkills";
import { Check, Cross, Shield, Send } from "../icons";

const ALL_STAGES: Stage[] = [...FUNNEL, "rejected"];

const INTENT: Record<ReplyIntent, { label: string; cls: string }> = {
  interested: { label: "interested", cls: "mint" },
  question: { label: "question", cls: "sky" },
  objection: { label: "objection", cls: "amber" },
  not_now: { label: "not now", cls: "slate" },
  opt_out: { label: "opt out", cls: "rose" },
};

export default function CandidateDrawer({
  pc,
  skill,
  onClose,
  onChanged,
}: {
  pc: PipelineCandidate;
  skill?: Skill;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [note, setNote] = useState("");
  const [stage, setStage] = useState<Stage>(pc.stage);
  const [notes, setNotes] = useState(pc.notes);
  const [suggestion, setSuggestion] = useState<ReplySuggestion | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

  const loadMsgs = () => api.candidateMessages(pc.id).then((r) => setMessages(r.messages)).catch(() => {});
  useEffect(() => {
    loadMsgs();
    setStage(pc.stage);
    setNotes(pc.notes);
    setSuggestion(null);
    setDraft("");
  }, [pc.id]);

  const move = async (s: Stage) => { setStage(s); await api.setStage(pc.id, s); onChanged(); };

  const inbound = async () => {
    setBusy(true);
    try {
      const r = await api.inbound(pc.id);
      setMessages(r.messages);
      setSuggestion(r.suggestion);
      setDraft(r.suggestion.body);
      setStage("replied");
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const send = async () => {
    if (!draft.trim() || !suggestion) return;
    setBusy(true);
    try {
      const r = await api.sendReply(pc.id, draft.trim(), suggestion.stage_hint);
      setMessages(r.messages);
      setStage(suggestion.stage_hint);
      setSuggestion(null);
      setDraft("");
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const addNote = async () => {
    if (!note.trim()) return;
    await api.addNote(pc.id, note.trim());
    setNotes((n) => [...n, { text: note.trim(), at: Date.now() / 1000 }]);
    setNote("");
    onChanged();
  };

  const verified = pc.claims.filter((c) => c.status === "verified");

  return (
    <div className="drawer-wrap">
      <div className="drawer-bg" onClick={onClose} />
      <div className="drawer">
        <div className="dh">
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <div className="k mono" style={{ fontSize: 11, color: "var(--muted)" }}>{pc.location} · {pc.language}</div>
            <button className="btn ghost" style={{ padding: "4px 10px" }} onClick={onClose}>✕</button>
          </div>
          <h2>{pc.name}</h2>
          <div style={{ marginTop: 6 }}>
            <span className={`badge ${pc.verdict === "advance" ? "mint" : pc.verdict === "reject" ? "rose" : "amber"}`}>
              {Math.round(pc.fit * 100)}% fit · {pc.verdict}
            </span>
            <span className="badge slate" style={{ marginLeft: 6 }}>{verified.length} proven claims</span>
          </div>
        </div>

        <div className="sec">
          <h4>Stage</h4>
          <div className="stagepick">
            {ALL_STAGES.map((s) => (
              <button key={s} className={stage === s ? "on" : ""} onClick={() => move(s)}>{stageLabel(skill, s)}</button>
            ))}
          </div>
        </div>

        <div className="sec">
          <h4>Grounded claims</h4>
          {pc.claims.map((c, i) => (
            <div key={i} className={`claim ${c.status === "verified" ? "ok" : "no"}`}>
              <span className="ic">{c.status === "verified" ? <Check /> : <Cross />}</span>
              <div>
                <div>{c.text}</div>
                <div className="ev">
                  {c.evidence.length > 0
                    ? c.evidence.map((e) => <span key={e.n}><span className="ln mono">L{e.n}</span>{e.text}</span>)
                    : <em>{c.reason}</em>}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="sec">
          <h4>Conversation</h4>
          {messages.length === 0 ? (
            <div style={{ fontSize: 12.5, color: "var(--faint)" }}>No messages yet. Outreach appears here once sent.</div>
          ) : (
            <div className="thread">
              {messages.map((m) => (
                <div key={m.id} className={`msg ${m.sender}`}>
                  <div className="who">{m.sender}</div>
                  {m.body}
                </div>
              ))}
            </div>
          )}

          {suggestion ? (
            <div className="suggest">
              <div className="sh">
                <span className="st"><Shield size={13} /> Karya drafted a grounded reply</span>
                <span className={`badge ${INTENT[suggestion.intent].cls}`}>{INTENT[suggestion.intent].label}</span>
              </div>
              <textarea className="sd" value={draft} onChange={(e) => setDraft(e.target.value)} rows={4} />
              {suggestion.grounded_on.length > 0 && (
                <div className="smeta">
                  <span className="sk">grounded on</span>
                  {suggestion.grounded_on.map((g) => <span className="gchip" key={g}>{g}</span>)}
                </div>
              )}
              {suggestion.dropped.length > 0 && (
                <div className="sdrop"><Cross size={12} /> guardrail removed unprovable mention of {suggestion.dropped.join(", ")}</div>
              )}
              <div className="sfoot">
                <span className="mono">tier {suggestion.tier} · {suggestion.requires_approval ? "needs your approval" : "auto"}</span>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn ghost" style={{ padding: "8px 13px" }} disabled={busy} onClick={() => { setSuggestion(null); setDraft(""); }}>Discard</button>
                  <button className="btn" style={{ padding: "8px 14px" }} disabled={busy || !draft.trim()} onClick={send}>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><Send size={13} /> Approve and send</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <button className="btn ghost" style={{ marginTop: 10, padding: "8px 14px" }} disabled={busy} onClick={inbound}>
              {busy ? "Reading the reply…" : "Simulate inbound reply"}
            </button>
          )}
        </div>

        <div className="sec notes">
          <h4>Notes</h4>
          {notes.map((n, i) => <div className="note" key={i}>{n.text}</div>)}
          <div className="noteadd">
            <input value={note} placeholder="Add a note…" onChange={(e) => setNote(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addNote()} />
            <button className="btn ghost" onClick={addNote}>Add</button>
          </div>
        </div>
      </div>
    </div>
  );
}
