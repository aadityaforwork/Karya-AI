import type {
  ApprovalQueueItem,
  Billing,
  CandidateDetail,
  Dashboard,
  Health,
  KaryaEvent,
  Message,
  PipelineCandidate,
  PoolFacets,
  ReplySuggestion,
  Role,
  RunCandidate,
  Skill,
  Stage,
  TalentItem,
  User,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

const TOKEN_KEY = "karya_token";
export const getToken = () => (typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY));
export const setToken = (t: string | null) => {
  if (typeof window === "undefined") return;
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
};

function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const t = getToken();
  return t ? { ...extra, Authorization: `Bearer ${t}` } : extra;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, { cache: "no-store", headers: authHeaders() });
  if (!r.ok) throw new ApiError(r.status, `${path} -> ${r.status}`);
  return r.json();
}

async function post<T>(path: string, body?: any): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(body !== undefined ? { "Content-Type": "application/json" } : {}),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new ApiError(r.status, data?.detail || `${path} -> ${r.status}`);
  return data;
}

export const api = {
  health: () => get<Health>("/api/health"),
  skills: () => get<{ skills: Skill[] }>("/api/skills"),
  plans: () => get<{ plans: import("./types").Plan[] }>("/api/plans"),

  // ---- auth ----
  signup: (body: { email: string; password: string; name?: string }) =>
    post<{ token: string; user: User }>("/api/auth/signup", body),
  login: (body: { email: string; password: string }) =>
    post<{ token: string; user: User }>("/api/auth/login", body),
  me: () => get<{ user: User }>("/api/auth/me"),

  // ---- billing ----
  billing: () => get<Billing>("/api/billing"),
  subscribe: (plan: string) => post<{ plan: string }>("/api/billing/subscribe", { plan }),

  // ---- runs / playground ----
  runEvents: (id: string) => get<{ events: KaryaEvent[] }>(`/api/runs/${id}/events`),
  runCandidates: (id: string) => get<{ candidates: RunCandidate[] }>(`/api/runs/${id}/candidates`),
  startGoal: (text: string) => post<{ run_id: string }>("/api/goals", { text }),
  approve: (approvalId: string, decision: boolean) => post<void>(`/api/approvals/${approvalId}`, { decision }),

  // ---- data pools ----
  talent: (pool = "talent") => get<{ talent: TalentItem[] }>(`/api/talent?pool=${pool}`),
  candidate: (id: string) => get<CandidateDetail>(`/api/talent/${id}`),
  poolFacets: (pool: string) => get<PoolFacets>(`/api/pools/${pool}/facets`),

  // ---- product ----
  dashboard: () => get<Dashboard>("/api/dashboard"),
  roles: () => get<{ roles: Role[] }>("/api/roles"),
  role: (id: string) => get<{ role: Role; runs: any[]; active_run: string | null }>(`/api/roles/${id}`),
  rolePipeline: (id: string) => get<{ pipeline: PipelineCandidate[] }>(`/api/roles/${id}/pipeline`),
  approvalsQueue: () => get<{ approvals: ApprovalQueueItem[] }>("/api/approvals"),
  candidateMessages: (pc: string) => get<{ messages: Message[] }>(`/api/candidates/${pc}/messages`),
  createRole: (body: Partial<Role>) => post<Role>("/api/roles", body),
  runRole: (id: string) => post<{ run_id: string; already_running: boolean }>(`/api/roles/${id}/run`),
  setStage: (pc: string, stage: Stage) => post(`/api/candidates/${pc}/stage`, { stage }),
  addNote: (pc: string, text: string) => post(`/api/candidates/${pc}/note`, { text }),
  reply: (pc: string) => post<{ messages: Message[] }>(`/api/candidates/${pc}/reply`),
  inbound: (pc: string, text?: string) =>
    post<{ messages: Message[]; suggestion: ReplySuggestion }>(
      `/api/candidates/${pc}/inbound`,
      text ? { text } : {},
    ),
  sendReply: (pc: string, body: string, stage?: string) =>
    post<{ messages: Message[] }>(`/api/candidates/${pc}/send`, { body, stage }),
};
