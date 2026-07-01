"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, API_BASE } from "./api";
import type { CostSnapshot, KaryaEvent, PendingApproval, PlanNodeView } from "./types";

export interface ScreenedView {
  candidate_id: string;
  name: string;
  language: string;
  fit: number;
  verdict: string;
  verified: string[];
  rejected: string[];
}

export interface Derived {
  status: string;
  cost: CostSnapshot;
  nodes: PlanNodeView[];
  pendingApproval: PendingApproval | null;
  report: Record<string, any> | null;
  screened: ScreenedView[];
  sourcedCount: number;
}

const EMPTY_COST: CostSnapshot = { total_usd: 0, by_tier: {}, calls_by_tier: {} };

export function derive(events: KaryaEvent[]): Derived {
  const names: Record<string, { name: string; language: string }> = {};
  const screenMap: Record<string, ScreenedView> = {};
  let nodes: PlanNodeView[] = [];
  let cost = EMPTY_COST;
  let report: Record<string, any> | null = null;
  let approvalReq: KaryaEvent | null = null;
  let approvalResolved = false;
  let status = events.length ? "running" : "idle";
  let sourcedCount = 0;

  for (const e of events) {
    switch (e.type) {
      case "plan.produced":
        nodes = (e.data.nodes || []).map((n: any) => ({ id: n.id, type: n.type, status: "pending" as const }));
        break;
      case "node.started":
        nodes = nodes.map((n) => (n.id === e.data.node ? { ...n, status: "running" } : n));
        break;
      case "node.completed":
        nodes = nodes.map((n) => (n.id === e.data.node ? { ...n, status: "done" } : n));
        break;
      case "node.failed":
        nodes = nodes.map((n) => (n.id === e.data.node ? { ...n, status: "failed" } : n));
        break;
      case "cost.accrued":
        cost = {
          total_usd: e.data.total_usd ?? cost.total_usd,
          by_tier: e.data.by_tier ?? cost.by_tier,
          calls_by_tier: e.data.calls_by_tier ?? cost.calls_by_tier,
        };
        break;
      case "candidate.sourced":
        sourcedCount += 1;
        names[e.data.candidate_id] = { name: e.data.name, language: e.data.language };
        break;
      case "candidate.screened":
        screenMap[e.data.candidate_id] = {
          candidate_id: e.data.candidate_id,
          name: names[e.data.candidate_id]?.name || e.data.candidate_id,
          language: names[e.data.candidate_id]?.language || "",
          fit: e.data.fit_score ?? 0,
          verdict: e.data.verdict ?? "",
          verified: e.data.verified ?? [],
          rejected: e.data.rejected ?? [],
        };
        break;
      case "approval.requested":
        approvalReq = e;
        approvalResolved = false;
        break;
      case "approval.granted":
      case "approval.denied":
        approvalResolved = true;
        break;
      case "run.completed":
        report = e.data;
        status = "done";
        break;
      case "run.failed":
        status = "failed";
        break;
    }
  }

  if (approvalReq && !approvalResolved) status = "awaiting_approval";
  const pendingApproval: PendingApproval | null =
    approvalReq && !approvalResolved
      ? { approval_id: approvalReq.data.approval_id, summary: approvalReq.title, drafts: approvalReq.data.drafts || [] }
      : null;

  const screened = Object.values(screenMap).sort((a, b) => b.fit - a.fit);
  return { status, cost, nodes, pendingApproval, report, screened, sourcedCount };
}

export function useKarya() {
  const [events, setEvents] = useState<KaryaEvent[]>([]);
  const [runId, setRunId] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!runId) return;
    const es = new EventSource(`${API_BASE}/api/stream/${runId}`);
    esRef.current = es;
    es.onmessage = (ev) => {
      try {
        const parsed: KaryaEvent = JSON.parse(ev.data);
        setEvents((prev) => (prev.some((p) => p.seq === parsed.seq) ? prev : [...prev, parsed]));
        if (parsed.type === "run.completed" || parsed.type === "run.failed") es.close();
      } catch {
        /* ignore pings */
      }
    };
    return () => es.close();
  }, [runId]);

  const startGoal = useCallback(async (text: string) => {
    setEvents([]);
    setRunId(null);
    const { run_id } = await api.startGoal(text);
    setRunId(run_id);
  }, []);

  const approve = useCallback((approvalId: string, decision: boolean) => api.approve(approvalId, decision), []);

  return { events, runId, derived: derive(events), startGoal, approve };
}
