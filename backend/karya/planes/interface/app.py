from __future__ import annotations

import asyncio
import json

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ...config import DATA_DIR, settings
from ...core.events import EventType, Level
from ...core.models import ApprovalStatus, Job
from ...engine import KaryaEngine
from ...product import plans
from ...product.auth import hash_password, make_token, verify_password, verify_token
from ...product.models import Role, RoleStatus, Stage, User
from ...product.skills import goal_text, list_skills, skill as skill_meta
from ...product.store import ProductStore

app = FastAPI(title="Karya", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = KaryaEngine()
store = ProductStore(DATA_DIR / "karya.db")

# run_id -> role_id / user_id, so a pending approval carries its context
_run_role: dict[str, str] = {}
_run_user: dict[str, str] = {}
# role_id -> the run currently in flight for it, so one workspace never has two
_role_active_run: dict[str, str] = {}
# Strong refs to the ingest tasks: asyncio only holds weak ones, so without this
# a run's results could be garbage-collected before they reach the pipeline.
_ingest_tasks: set[asyncio.Task] = set()

TERMINAL = {EventType.RUN_COMPLETED, EventType.RUN_FAILED}


def current_user(authorization: str = Header(default="")) -> User:
    uid = verify_token(authorization.removeprefix("Bearer ").strip())
    user = store.get_user(uid) if uid else None
    if not user:
        raise HTTPException(401, "not authenticated")
    return user

EXAMPLES = [
    "Hire 2 backend engineers in Pune",
    "Hire 1 senior backend engineer in Bangalore",
    "Hire 3 full-stack engineers in Mumbai",
]


class GoalIn(BaseModel):
    text: str


class ApprovalIn(BaseModel):
    decision: bool


class RoleIn(BaseModel):
    skill: str = "hiring"
    title: str
    location: str
    headcount: int = 1
    must_have: list[str] = []
    nice_to_have: list[str] = []
    seniority: str = "mid"


class NoteIn(BaseModel):
    text: str


class StageIn(BaseModel):
    stage: str


class InboundIn(BaseModel):
    text: str | None = None


class SendIn(BaseModel):
    body: str
    stage: str | None = None


class SignupIn(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class SubscribeIn(BaseModel):
    plan: str


DEMO_EMAIL = "demo@karya.ai"
DEMO_PASSWORD = "demo1234"


@app.on_event("startup")
def _seed_demo() -> None:
    if store.user_by_email(DEMO_EMAIL):
        return
    h, salt = hash_password(DEMO_PASSWORD)
    user = store.create_user(
        User(email=DEMO_EMAIL, name="Demo recruiter", password_hash=h, salt=salt, plan="pro")
    )
    for sk in ("hiring", "sales"):
        store.create_role(Role(user_id=user.id, skill=sk, **skill_meta(sk)["default_spec"]))


def _seed_starter(user: User) -> None:
    store.create_role(Role(user_id=user.id, skill="hiring", **skill_meta("hiring")["default_spec"]))


# ---- auth ----


@app.post("/api/auth/signup")
def signup(body: SignupIn) -> dict:
    email = body.email.strip().lower()
    if not email or not body.password:
        raise HTTPException(400, "email and password required")
    if store.user_by_email(email):
        raise HTTPException(409, "an account with that email already exists")
    h, salt = hash_password(body.password)
    user = store.create_user(User(email=email, name=body.name.strip(), password_hash=h, salt=salt, plan="free"))
    _seed_starter(user)
    return {"token": make_token(user.id), "user": user.public()}


@app.post("/api/auth/login")
def login(body: LoginIn) -> dict:
    user = store.user_by_email(body.email.strip().lower())
    if not user or not verify_password(body.password, user.password_hash, user.salt):
        raise HTTPException(401, "invalid email or password")
    return {"token": make_token(user.id), "user": user.public()}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"user": user.public()}


# ---- billing ----


@app.get("/api/billing")
def billing(user: User = Depends(current_user)) -> dict:
    p = plans.plan(user.plan)
    return {
        "plan": user.plan,
        "plans": [plans.plan(pid) for pid in plans.ORDER],
        "usage": {
            "workspaces": store.count_workspaces(user.id),
            "workspace_limit": p["workspaces"],
            "runs": store.count_runs(user.id),
            "runs_limit": p["runs_per_month"],
        },
    }


@app.post("/api/billing/subscribe")
def subscribe(body: SubscribeIn, user: User = Depends(current_user)) -> dict:
    if body.plan not in plans.PLANS:
        raise HTTPException(400, "unknown plan")
    store.set_plan(user.id, body.plan)  # mock checkout: real processor slots in here
    return {"plan": body.plan}


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "engine": "mock" if settings.use_mock else "openai",
        "tiers": [{"tier": t.tier, "model": t.model} for t in settings.tiers],
        "gate_tau": settings.gate_tau,
    }


@app.get("/api/examples")
def examples() -> dict:
    return {"examples": EXAMPLES}


@app.post("/api/goals")
async def create_goal(body: GoalIn, user: User = Depends(current_user)) -> dict:
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "goal text required")
    goal = engine.start_goal(text)  # schedules the run on this event loop
    _run_user[goal.id] = user.id
    return {"run_id": goal.id, "goal": goal.model_dump()}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict:
    ctx = engine.run_context(run_id)
    if ctx is None:
        raise HTTPException(404, "run not found")
    return {
        "run_id": run_id,
        "status": ctx.goal.status.value,
        "goal": ctx.goal.text,
        "job": ctx.job.model_dump() if ctx.job else None,
        "finalists": [c.name for c in ctx.finalists],
        "report": ctx.report or None,
        "cost": engine.state.ledger.snapshot(run_id),
        "pending_approvals": [
            a.model_dump() for a in engine.state.entities.pending_approvals(run_id)
        ],
    }


@app.get("/api/runs/{run_id}/events")
def get_events(run_id: str) -> dict:
    return {"events": [e.model_dump() for e in engine.state.events.history(run_id)]}


@app.get("/api/runs")
def list_runs() -> dict:
    return {"runs": engine.list_runs()}


@app.get("/api/runs/{run_id}/candidates")
def run_candidates(run_id: str) -> dict:
    data = engine.run_candidates(run_id)
    if data is None:
        raise HTTPException(404, "run not found")
    return {"candidates": data}


@app.get("/api/talent")
def talent(pool: str = "talent", user: User = Depends(current_user)) -> dict:
    return {"talent": engine.talent(pool)}


@app.get("/api/pools/{pool}/facets")
def pool_facets(pool: str, user: User = Depends(current_user)) -> dict:
    return engine.pool_facets(pool)


@app.get("/api/talent/{candidate_id}")
def talent_detail(candidate_id: str, user: User = Depends(current_user)) -> dict:
    data = engine.candidate(candidate_id)
    if data is None:
        raise HTTPException(404, "candidate not found")
    return data


@app.post("/api/approvals/{approval_id}")
async def decide_approval(approval_id: str, body: ApprovalIn, user: User = Depends(current_user)) -> dict:
    existing = engine.state.entities.approval(approval_id)
    if existing and _run_user.get(existing.run_id) not in (None, user.id):
        raise HTTPException(403, "not your approval")
    if existing and existing.status == ApprovalStatus.PENDING and not engine.approval_is_live(approval_id):
        # The run that opened this gate is gone (server restarted). Stamping it
        # approved would look like it worked while nothing sent.
        raise HTTPException(409, "that run is no longer active - start a new run to send this outreach")
    approval = engine.approve(approval_id, body.decision)
    if approval is None:
        raise HTTPException(404, "approval not found")
    return {"approval": approval.model_dump()}


# ---- product: skills, workspaces, pipeline, inbox, approvals, dashboard ----


@app.get("/api/skills")
def skills() -> dict:
    return {"skills": list_skills()}


@app.get("/api/plans")
def public_plans() -> dict:
    return {"plans": [plans.plan(p) for p in plans.ORDER]}


@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user)) -> dict:
    return store.dashboard(user.id)


def _require_role(role_id: str, user: User) -> Role:
    role = store.role(role_id)
    if not role or role.user_id != user.id:
        raise HTTPException(404, "workspace not found")
    return role


def _require_pc(pc_id: str, user: User):
    pc = store.candidate(pc_id)
    if not pc or pc.user_id != user.id:
        raise HTTPException(404, "candidate not found")
    return pc


@app.get("/api/roles")
def list_roles(user: User = Depends(current_user)) -> dict:
    out = []
    for r in store.roles(user.id):
        pipe = store.pipeline(r.id)
        out.append({**r.model_dump(), "pipeline_count": len(pipe),
                    "contacted": sum(1 for p in pipe if p.stage.value in ("contacted", "replied", "interview", "offer"))})
    return {"roles": out}


@app.post("/api/roles")
def create_role(body: RoleIn, user: User = Depends(current_user)) -> dict:
    if not plans.skill_allowed(user.plan, body.skill):
        raise HTTPException(402, f"the {body.skill} skill needs a higher plan")
    if not plans.can_add_workspace(user.plan, store.count_workspaces(user.id)):
        raise HTTPException(402, "workspace limit reached on your plan")
    role = store.create_role(Role(user_id=user.id, **body.model_dump()))
    return role.model_dump()


@app.get("/api/roles/{role_id}")
def get_role(role_id: str, user: User = Depends(current_user)) -> dict:
    role = _require_role(role_id, user)
    # Hand back any run still in flight so a reload can rejoin its live feed
    # instead of dropping the user on a board that looks idle.
    active = _role_active_run.get(role_id)
    if active and not engine.is_run_active(active):
        active = None
    return {"role": role.model_dump(), "runs": store.runs(role_id), "active_run": active}


@app.post("/api/roles/{role_id}/close")
def close_role(role_id: str, user: User = Depends(current_user)) -> dict:
    _require_role(role_id, user)
    store.set_role_status(role_id, RoleStatus.CLOSED)
    return {"ok": True}


@app.get("/api/roles/{role_id}/pipeline")
def role_pipeline(role_id: str, user: User = Depends(current_user)) -> dict:
    _require_role(role_id, user)
    return {"pipeline": [p.model_dump() for p in store.pipeline(role_id)]}


@app.post("/api/roles/{role_id}/run")
async def run_role(role_id: str, user: User = Depends(current_user)) -> dict:
    role = _require_role(role_id, user)

    # Re-running a workspace that is already working returns the run in flight
    # rather than starting a second one. The old behaviour let an impatient
    # second click double every candidate in the pipeline and open two approvals.
    active = _role_active_run.get(role_id)
    if active and engine.is_run_active(active):
        return {"run_id": active, "already_running": True}

    if not plans.can_run(user.plan, store.count_runs(user.id)):
        raise HTTPException(402, "monthly run limit reached on your plan")

    meta = skill_meta(role.skill)
    job = Job(
        id=role.id, title=role.title, location=role.location, headcount=role.headcount,
        must_have=role.must_have, nice_to_have=role.nice_to_have, seniority=role.seniority,
        pool=meta["pool"],
    )
    text = goal_text(role.skill, role.title, role.headcount, role.location)
    goal = engine.start_goal_for_job(text, job)
    _run_role[goal.id] = role_id
    _run_user[goal.id] = user.id
    _role_active_run[role_id] = goal.id
    task = asyncio.create_task(_ingest_after(role_id, goal.id, user.id))
    _ingest_tasks.add(task)
    task.add_done_callback(_ingest_tasks.discard)
    return {"run_id": goal.id, "already_running": False}


async def _ingest_after(role_id: str, run_id: str, user_id: str) -> None:
    """Wait for the run, then land its results in the durable pipeline.

    Everything here is best-effort but must never die silently: this is the only
    path by which a run's candidates reach the workspace board.
    """
    try:
        task = engine.task(run_id)
        if task:
            await task
        ctx = engine.run_context(run_id)
        if ctx is None or not ctx.report:
            return
        candidates = engine.run_candidates(run_id) or []
        drafts = [
            {"candidate_id": d.candidate_id, "subject": d.subject, "body": d.body,
             "language": d.language.value, "sent": d.sent}
            for d in ctx.drafts
        ]
        store.ingest_run(role_id, run_id, user_id=user_id, goal=ctx.goal.text, report=ctx.report,
                         candidates=candidates, drafts=drafts)
    except Exception as error:  # noqa: BLE001
        # Surface it on the run's own feed so the failure is visible in the UI
        # rather than vanishing into a discarded task.
        engine.state.emit(
            run_id, EventType.RUN_FAILED, f"could not save results to the workspace: {error}",
            {"error": str(error)}, level=Level.ERROR,
        )
    finally:
        if _role_active_run.get(role_id) == run_id:
            _role_active_run.pop(role_id, None)


@app.post("/api/candidates/{pc_id}/stage")
def set_candidate_stage(pc_id: str, body: StageIn, user: User = Depends(current_user)) -> dict:
    _require_pc(pc_id, user)
    try:
        stage = Stage(body.stage)
    except ValueError:
        raise HTTPException(400, "invalid stage")
    return store.set_stage(pc_id, stage).model_dump()


@app.post("/api/candidates/{pc_id}/note")
def add_candidate_note(pc_id: str, body: NoteIn, user: User = Depends(current_user)) -> dict:
    _require_pc(pc_id, user)
    return store.add_note(pc_id, body.text).model_dump()


@app.get("/api/candidates/{pc_id}/messages")
def candidate_messages(pc_id: str, user: User = Depends(current_user)) -> dict:
    _require_pc(pc_id, user)
    return {"messages": [m.model_dump() for m in store.messages(pc_id)]}


@app.post("/api/candidates/{pc_id}/reply")
def candidate_reply(pc_id: str, user: User = Depends(current_user)) -> dict:
    _require_pc(pc_id, user)
    return store.simulate_reply(pc_id)


@app.post("/api/candidates/{pc_id}/inbound")
async def candidate_inbound(pc_id: str, body: InboundIn, user: User = Depends(current_user)) -> dict:
    pc = _require_pc(pc_id, user)
    role = store.role(pc.role_id)
    text = (body.text or "").strip() or store.sample_inbound(pc, role)
    store.record_inbound(pc_id, text)
    pc = store.candidate(pc_id)
    proven = [c.get("text", "") for c in pc.claims if c.get("status") == "verified"]
    role_facts = {
        "title": role.title if role else "",
        "location": role.location if role else "",
        "must_have": role.must_have if role else [],
        "nice_to_have": role.nice_to_have if role else [],
        "seniority": role.seniority if role else "",
    }
    history = [{"sender": m.sender, "body": m.body} for m in store.messages(pc_id)]
    suggestion = await engine.suggest_reply(
        pc_id=pc_id, name=pc.name, language=pc.language, proven_facts=proven,
        role_facts=role_facts, history=history, inbound=text,
    )
    return {"messages": [m.model_dump() for m in store.messages(pc_id)], "suggestion": suggestion}


@app.post("/api/candidates/{pc_id}/send")
def candidate_send(pc_id: str, body: SendIn, user: User = Depends(current_user)) -> dict:
    _require_pc(pc_id, user)
    text = body.body.strip()
    if not text:
        raise HTTPException(400, "empty message")
    result = store.send_reply(pc_id, text, body.stage)
    if result is None:
        raise HTTPException(404, "candidate not found")
    return result


@app.get("/api/approvals")
def approvals_queue(user: User = Depends(current_user)) -> dict:
    out = []
    for a in engine.state.entities.approvals.values():
        if a.status.value != "pending" or _run_user.get(a.run_id) != user.id:
            continue
        role_id = _run_role.get(a.run_id)
        role = store.role(role_id) if role_id else None
        ctx = engine.run_context(a.run_id)
        out.append({
            **a.model_dump(),
            "role_id": role_id,
            "role_title": role.title if role else None,
            "goal": ctx.goal.text if ctx else None,
        })
    return {"approvals": out}


@app.get("/api/stream/{run_id}")
async def stream(run_id: str) -> EventSourceResponse:
    log = engine.state.events

    async def gen():
        q = log.subscribe(run_id)
        seen = 0
        try:
            for ev in log.history(run_id):
                seen = max(seen, ev.seq)
                yield _sse(ev)
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
                    continue
                if ev.seq <= seen:
                    continue
                seen = ev.seq
                yield _sse(ev)
                if ev.type in TERMINAL:
                    break
        finally:
            log.unsubscribe(run_id, q)

    return EventSourceResponse(gen())


def _sse(ev) -> dict:
    # Deliberately unnamed (default "message") so the browser's EventSource.onmessage
    # receives every event. The event type travels inside the JSON payload.
    return {"id": str(ev.seq), "data": json.dumps(ev.model_dump(), default=str)}
