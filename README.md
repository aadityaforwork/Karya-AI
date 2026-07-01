# Karya

**An AI-workforce platform. Describe an outcome; a team of AI workers does the job - cheaply, with proof, in any language.**

Karya is a *platform*, not a single tool. The same infrastructure - a cost-aware
language-aware model router, an evidence verifier that makes hallucinated claims
impossible to keep, a human approval gate, and durable state - runs multiple
**skills**:

- **Hiring** - *"Hire 2 backend engineers in Pune"* → candidates sourced, screened with
  every claim grounded in a résumé line, outreach drafted, one approval, sent, reported.
- **Sales outreach** - *"Reach 2 prospects matching fintech leaders in Bengaluru"* → the
  **same engine**, a different data pool. (Hiring and sales are isomorphic: a prospect is
  a candidate, an ICP is a job, company facts are résumé lines, signals are skills.)
- **Support triage**, **Research** - stubs that prove the platform generalises.

You work in **workspaces** (a role for hiring, a campaign for sales), each with its own
persistent pipeline. The architecture is the five planes from the deck; everything runs
at roughly 1/9th the cost of using a frontier model for everything.

---

## The architecture (five planes)

```
Interface     goal input · live activity feed · approval queue
Orchestration planner · DAG validator · scheduler · reflector
Execution     cost-aware router (tier 0→2) · sourcing / screening / outreach agents · tool sandbox
Trust         verifier (evidence entailment) · policy engine · idempotency guard
State         event log · evidence store · entity store
```

Each plane talks only to the one below it; nothing reaches the State plane except
through the Trust plane. The activity feed is just the append-only event log, streamed.

### The three mechanics that make it work

1. **Cheapest model that can be trusted.** The router starts on a cheap model and
   escalates to a smarter one only when confidence is below the gate (`tau`). It also
   routes by **language**: cheap models are weak in Marathi/Telugu, so those tasks
   *start* on a smarter tier instead of wasting a doomed cheap call. The verifier's
   outcomes feed back into the per-language routing priors over time.
2. **No answer without proof.** Every claim a worker makes must cite exact résumé
   lines. The verifier rejects anything not entailed by the cited evidence - a claim
   like *"10 years of Kubernetes"* is bounced when the cited line doesn't support it,
   re-retrieved, and dropped if it still can't be grounded.
3. **A human approves what matters.** The boring 95% runs autonomously; an external
   send (real consequences) blocks for one-tap approval.

---

## Run it

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate           # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env           # then put your OPENAI_API_KEY in .env
python run.py                    # serves http://127.0.0.1:8000
```

- **Real engine:** set `OPENAI_API_KEY` in `.env`. Model calls run through
  **LangChain** (`ChatOpenAI`); tier 0/1/2 map to `gpt-4o-mini` / `gpt-4o` / `gpt-4o`
  (configurable in `.env`).
- **Mock engine:** leave the key blank or set `KARYA_FORCE_MOCK=true`. The whole
  system runs deterministically offline - same planes, same trust loop, same cost math.

Try it without the server:

```bash
python demo.py "Hire 2 backend engineers in Pune"   # prints the live feed in the terminal
pytest -q                                            # 11 tests
```

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev                      # serves http://localhost:3000
```

It reads `NEXT_PUBLIC_API_BASE` (defaults to `http://127.0.0.1:8000`) from `.env.local`.

**Accounts & plans.** The app is behind login (email + password, hashed; signed-token
auth; per-user workspaces). A seeded demo account is ready: **`demo@karya.ai` / `demo1234`**
(prefilled on the login page). Subscription plans - **Free / Pro / Business** - gate
features (Free = 1 workspace + Hiring only; Pro adds Sales; Business unlocks everything).
Checkout is mocked (a real processor slots in behind `/api/billing/subscribe`).

Public pages: **`/`** (landing), **`/pricing`**, **`/login`**, **`/signup`**.
App pages (behind auth):
- **Home** (`/app`) - platform launcher: skill cards, workspace pulse (saved $, hours, pipeline, proven claims), funnel, spend + language mix.
- **Workspaces** (`/roles`, `/roles/[id]`) - skill-aware list + create; a workspace detail is a **pipeline board** (Sourced → … → Offer/Won) with a candidate drawer (stage control, grounded claims with cited lines, inbox thread, notes).
- **Approvals** (`/approvals`) - every pending external send across all workspaces, one tap each.
- **Playground** (`/playground`) - run any free-form goal and watch the engine live.
- **Settings** (`/settings`) - engine/tiers, gate, trust + approval policy, language routing, skill catalogue.
- **How it works** (`/how-it-works`) - the five planes, the three rules, the language routing table.
- **Talent** (`/talent`) - browse a data pool and its numbered profiles (the evidence).

---

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/goals` | start a goal → `{ run_id }` |
| `GET`  | `/api/stream/{run_id}` | SSE activity feed |
| `POST` | `/api/approvals/{approval_id}` | `{ "decision": true \| false }` |
| `GET`  | `/api/skills` | the platform's skill catalogue |
| `GET`  | `/api/dashboard` | workspace-wide KPIs (per-skill, funnel, cost, hours) |
| `GET` `POST` | `/api/roles` · `/api/roles/{id}` | workspaces (a role/campaign per skill) |
| `POST` | `/api/roles/{id}/run` | run the skill against its pool → run_id |
| `GET`  | `/api/roles/{id}/pipeline` | the workspace's pipeline |
| `POST` | `/api/candidates/{id}/{stage,note,reply}` | work a pipeline item |
| `GET`  | `/api/approvals` | pending sends across all workspaces |
| `GET`  | `/api/runs/{run_id}/candidates` | screening detail with evidence resolved to text |
| `GET`  | `/api/talent?pool=talent\|prospects` | a data pool + profiles |
| `GET`  | `/api/health` | engine + tier config |

---

## Layout

```
backend/
  karya/
    core/                 events, domain models, ids
    planes/
      state/              event log, evidence store, entity store, cost ledger
      trust/              verifier, policy engine, idempotency guard
      execution/          llm client, router, agents, tool sandbox
      orchestration/      planner, dag validator, scheduler, reflector
      interface/          FastAPI app + SSE
    engine.py             wires the five planes; runs a goal end to end
  data/seed.py            synthetic multi-language talent pool
  demo.py                 terminal run · tests/  pytest suite
frontend/
  app/                    routes: console (/), runs, runs/[id], talent, how-it-works
  components/             Nav + console/ (pipeline, feed, cost, candidates, approval, report)
  lib/                    api client, types, useKarya (SSE hook + state derivation)
```
