export type Level = "info" | "success" | "warn" | "error";
export type Plane = "interface" | "orchestration" | "execution" | "trust" | "state";

export interface KaryaEvent {
  id: string;
  seq: number;
  run_id: string;
  ts: number;
  type: string;
  plane: Plane;
  level: Level;
  title: string;
  data: Record<string, any>;
}

export interface CostSnapshot {
  total_usd: number;
  by_tier: Record<string, number>;
  calls_by_tier: Record<string, number>;
}

export interface PlanNodeView {
  id: string;
  type: string;
  status: "pending" | "running" | "done" | "failed";
}

export interface DraftView {
  candidate_id: string;
  subject: string;
  body: string;
  language: string;
  cited_facts: string[];
}

export interface PendingApproval {
  approval_id: string;
  summary: string;
  drafts: DraftView[];
}

export interface Health {
  engine: "mock" | "openai";
  tiers: { tier: number; model: string }[];
  gate_tau: number;
}

export interface RunSummary {
  run_id: string;
  goal: string;
  status: string;
  created_at: number;
  job_title: string | null;
  location: string | null;
  sourced: number;
  finalists: string[];
  sent: number;
  cost_usd: number | null;
}

export interface TalentItem {
  id: string;
  name: string;
  headline: string;
  location: string;
  language: string;
  years_experience: number;
  skills: string[];
  resume_lines: number;
}

export interface PoolFacet { name: string; count: number }

/** What a data pool can actually be asked for. Drives the workspace form so a
 *  spec cannot be written against skills nobody in the pool has. */
export interface PoolFacets {
  pool: string;
  size: number;
  skills: PoolFacet[];
  locations: PoolFacet[];
}

/** Present on a run report when sourcing matched nobody. */
export interface NoMatch {
  pool: string;
  pool_size: number;
  requested: string[];
  location: string;
  available_skills: string[];
}

export interface ResumeLine { n: number; text: string }

export interface CandidateDetail extends TalentItem {
  resume: ResumeLine[];
}

export interface EvidenceRef { n: number; text: string }
export interface ClaimDetail {
  text: string;
  status: "proposed" | "verified" | "rejected";
  reason: string;
  evidence: EvidenceRef[];
}
export interface RunCandidate {
  candidate_id: string;
  name: string;
  language: string;
  location: string;
  fit_score: number;
  verdict: string;
  is_finalist: boolean;
  claims: ClaimDetail[];
}

export type Stage = "sourced" | "screened" | "contacted" | "replied" | "interview" | "offer" | "rejected";

export const FUNNEL: Stage[] = ["sourced", "screened", "contacted", "replied", "interview", "offer"];
export const STAGE_LABEL: Record<Stage, string> = {
  sourced: "Sourced",
  screened: "Screened",
  contacted: "Contacted",
  replied: "Replied",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
};

export interface User {
  id: string;
  email: string;
  name: string;
  plan: string;
}

export interface Plan {
  id: string;
  name: string;
  price_usd: number;
  price_inr: number;
  tagline: string;
  workspaces: number;
  runs_per_month: number;
  skills: string[];
  features: string[];
}

export interface Billing {
  plan: string;
  plans: Plan[];
  usage: { workspaces: number; workspace_limit: number; runs: number; runs_limit: number };
}

export interface Skill {
  id: string;
  name: string;
  tagline: string;
  active: boolean;
  pool: string;
  entity: string;
  entity_plural: string;
  spec: string;
  spec_plural: string;
  accent: string;
  stage_labels: Record<string, string>;
  default_spec: any;
}

export interface Role {
  id: string;
  skill: string;
  title: string;
  location: string;
  headcount: number;
  must_have: string[];
  nice_to_have: string[];
  seniority: string;
  status: "open" | "closed";
  created_at: number;
  pipeline_count?: number;
  contacted?: number;
}

export interface PipelineCandidate {
  id: string;
  role_id: string;
  candidate_id: string;
  name: string;
  language: string;
  location: string;
  fit: number;
  verdict: string;
  stage: Stage;
  claims: ClaimDetail[];
  notes: { text: string; at: number }[];
  run_id: string;
}

export interface Message {
  id: string;
  pipeline_id: string;
  sender: "karya" | "candidate" | "system";
  channel: string;
  language: string;
  body: string;
  created_at: number;
}

export type ReplyIntent = "interested" | "question" | "objection" | "not_now" | "opt_out";

export interface ReplySuggestion {
  intent: ReplyIntent;
  body: string;
  grounded_on: string[];
  dropped: string[];
  stage_hint: Stage;
  requires_approval: boolean;
  confidence: number;
  tier: number;
  model: string;
  cost_usd: number;
  mock: boolean;
}

export interface ApprovalQueueItem {
  id: string;
  run_id: string;
  role_id: string | null;
  role_title: string | null;
  goal: string | null;
  summary: string;
  risk_tier: number;
  payload: { drafts: DraftView[] };
}

export interface Dashboard {
  roles: { total: number; open: number };
  pipeline: { total: number; funnel: Record<string, number> };
  runs: number;
  outreach_sent: number;
  candidates_sourced: number;
  claims: { verified: number; rejected: number };
  cost: { karya_usd: number; frontier_only_usd: number; saved_usd: number; savings_x: number | null };
  tier_calls: Record<string, number>;
  language_mix: Record<string, number>;
  hours_saved: number;
  by_skill: Record<string, { roles: number; pipeline: number; contacted: number }>;
}

export const PLANE_COLOR: Record<Plane, string> = {
  interface: "var(--sky)",
  orchestration: "var(--teal)",
  execution: "var(--mint)",
  trust: "var(--amber)",
  state: "var(--slate)",
};
