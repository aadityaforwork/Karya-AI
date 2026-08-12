from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .db import Database
from .models import FUNNEL, Message, PipelineCandidate, Role, RoleStatus, RunRecord, Stage, User

# rough minutes a human would spend per action, for the "time saved" story
MIN_PER_SOURCED = 6
MIN_PER_SCREENED = 12
MIN_PER_OUTREACH = 8


def _further_stage(current: Stage, incoming: Stage) -> Stage:
    """The later of two stages along the funnel.

    A human's manual progress outranks a re-run's fresh screening verdict, but a
    fresh run may still reject someone, and may revive a previously rejected
    candidate whose evidence now holds up.
    """
    if current == Stage.REJECTED or incoming == Stage.REJECTED:
        return incoming
    order = {s: i for i, s in enumerate(FUNNEL)}
    return current if order.get(current, 0) >= order.get(incoming, 0) else incoming


def _loads(v: str | None, default):
    if not v:
        return default
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return default


class ProductStore:
    """Durable recruiting workspace that sits on top of the run engine."""

    def __init__(self, path: str | Path) -> None:
        self.db = Database(path)

    # ----- users -----

    def _user(self, row) -> User:
        return User(
            id=row["id"], email=row["email"], name=row["name"] or "",
            password_hash=row["password_hash"], salt=row["salt"],
            plan=row["plan"] or "free", created_at=row["created_at"],
        )

    def create_user(self, user: User) -> User:
        user.created_at = user.created_at or time.time()
        self.db.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
            (user.id, user.email.lower(), user.name, user.password_hash, user.salt, user.plan, user.created_at),
        )
        return user

    def user_by_email(self, email: str) -> User | None:
        row = self.db.one("SELECT * FROM users WHERE email=?", (email.lower(),))
        return self._user(row) if row else None

    def get_user(self, user_id: str) -> User | None:
        row = self.db.one("SELECT * FROM users WHERE id=?", (user_id,))
        return self._user(row) if row else None

    def set_plan(self, user_id: str, plan: str) -> None:
        self.db.execute("UPDATE users SET plan=? WHERE id=?", (plan, user_id))

    def count_workspaces(self, user_id: str) -> int:
        row = self.db.one("SELECT COUNT(*) c FROM roles WHERE user_id=?", (user_id,))
        return row["c"] if row else 0

    def count_runs(self, user_id: str) -> int:
        row = self.db.one("SELECT COUNT(*) c FROM runs WHERE user_id=?", (user_id,))
        return row["c"] if row else 0

    # ----- roles (workspaces) -----

    def create_role(self, role: Role) -> Role:
        role.created_at = role.created_at or time.time()
        self.db.execute(
            "INSERT INTO roles VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                role.id, role.user_id, role.skill, role.title, role.location, role.headcount,
                json.dumps(role.must_have), json.dumps(role.nice_to_have),
                role.seniority, role.status.value, role.created_at,
            ),
        )
        return role

    def _role(self, row) -> Role:
        return Role(
            id=row["id"], user_id=row["user_id"] or "", skill=row["skill"] or "hiring",
            title=row["title"], location=row["location"], headcount=row["headcount"],
            must_have=_loads(row["must_have"], []), nice_to_have=_loads(row["nice_to_have"], []),
            seniority=row["seniority"], status=RoleStatus(row["status"]), created_at=row["created_at"],
        )

    def roles(self, user_id: str) -> list[Role]:
        rows = self.db.query("SELECT * FROM roles WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        return [self._role(r) for r in rows]

    def role(self, role_id: str) -> Role | None:
        row = self.db.one("SELECT * FROM roles WHERE id=?", (role_id,))
        return self._role(row) if row else None

    def set_role_status(self, role_id: str, status: RoleStatus) -> None:
        self.db.execute("UPDATE roles SET status=? WHERE id=?", (status.value, role_id))

    # ----- pipeline -----

    def _pc(self, row) -> PipelineCandidate:
        return PipelineCandidate(
            id=row["id"], user_id=row["user_id"] or "", role_id=row["role_id"],
            candidate_id=row["candidate_id"], name=row["name"],
            language=row["language"], location=row["location"], fit=row["fit"], verdict=row["verdict"],
            stage=Stage(row["stage"]), claims=_loads(row["claims"], []), notes=_loads(row["notes"], []),
            run_id=row["run_id"], created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def _insert_pc(self, pc: PipelineCandidate) -> None:
        self.db.execute(
            "INSERT INTO pipeline VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                pc.id, pc.user_id, pc.role_id, pc.candidate_id, pc.name, pc.language, pc.location,
                pc.fit, pc.verdict, pc.stage.value, json.dumps(pc.claims), json.dumps(pc.notes),
                pc.run_id, pc.created_at, pc.updated_at,
            ),
        )

    def _upsert_pc(self, pc: PipelineCandidate) -> str:
        """Insert the candidate, or refresh the row that already tracks them.

        A workspace can be run many times against the same pool, so the same
        person is sourced again and again. Inserting blindly stacked duplicate
        cards in every column. Re-running now refreshes the evidence and keeps
        the human's own work: notes are preserved, and someone already moved to
        Interview is never dragged back to Screened by a fresh run.
        """
        row = self.db.one(
            "SELECT * FROM pipeline WHERE role_id=? AND candidate_id=?",
            (pc.role_id, pc.candidate_id),
        )
        if row is None:
            self._insert_pc(pc)
            return pc.id

        current = self._pc(row)
        self.db.execute(
            "UPDATE pipeline SET name=?, language=?, location=?, fit=?, verdict=?, stage=?, "
            "claims=?, run_id=?, updated_at=? WHERE id=?",
            (
                pc.name, pc.language, pc.location, pc.fit, pc.verdict,
                _further_stage(current.stage, pc.stage).value,
                json.dumps(pc.claims), pc.run_id, pc.updated_at, current.id,
            ),
        )
        return current.id

    def pipeline(self, role_id: str) -> list[PipelineCandidate]:
        rows = self.db.query("SELECT * FROM pipeline WHERE role_id=? ORDER BY fit DESC", (role_id,))
        return [self._pc(r) for r in rows]

    def candidate(self, pc_id: str) -> PipelineCandidate | None:
        row = self.db.one("SELECT * FROM pipeline WHERE id=?", (pc_id,))
        return self._pc(row) if row else None

    def set_stage(self, pc_id: str, stage: Stage) -> PipelineCandidate | None:
        self.db.execute("UPDATE pipeline SET stage=?, updated_at=? WHERE id=?", (stage.value, time.time(), pc_id))
        return self.candidate(pc_id)

    def add_note(self, pc_id: str, text: str) -> PipelineCandidate | None:
        pc = self.candidate(pc_id)
        if not pc:
            return None
        pc.notes.append({"text": text, "at": time.time()})
        self.db.execute("UPDATE pipeline SET notes=?, updated_at=? WHERE id=?", (json.dumps(pc.notes), time.time(), pc_id))
        return self.candidate(pc_id)

    # ----- messages -----

    def messages(self, pc_id: str) -> list[Message]:
        rows = self.db.query("SELECT * FROM messages WHERE pipeline_id=? ORDER BY created_at ASC", (pc_id,))
        return [
            Message(id=r["id"], pipeline_id=r["pipeline_id"], sender=r["sender"], channel=r["channel"],
                    language=r["language"], body=r["body"], created_at=r["created_at"])
            for r in rows
        ]

    def add_message(self, msg: Message) -> Message:
        msg.created_at = msg.created_at or time.time()
        self.db.execute(
            "INSERT INTO messages VALUES (?,?,?,?,?,?,?)",
            (msg.id, msg.pipeline_id, msg.sender, msg.channel, msg.language, msg.body, msg.created_at),
        )
        return msg

    def sample_inbound(self, pc: PipelineCandidate, role: Role | None) -> str:
        """A realistic inbound reply. Walks through a tough question, then an
        objection, then a yes, so repeated demos show the grounding holding up."""
        first = pc.name.split()[0]
        if pc.language != "en":
            localized = {
                "hi": f"नमस्ते, संपर्क करने के लिए धन्यवाद। हाँ, मैं एक छोटी कॉल के लिए तैयार हूँ। - {first}",
                "mr": f"नमस्कार, संपर्क केल्याबद्दल धन्यवाद. हो, मी एका छोट्या कॉलसाठी तयार आहे. - {first}",
                "te": f"నమస్కారం, సంప్రదించినందుకు ధన్యవాదాలు. అవును, ఒక చిన్న కాల్‌కు సిద్ధంగా ఉన్నాను. - {first}",
            }
            return localized.get(pc.language, "Thanks, happy to talk.")

        must = role.must_have if role else []
        nice = role.nice_to_have if role else []
        known = must[0] if must else "the core stack"
        owned = {s.lower() for s in must + nice}
        unknown = next((t for t in ("Rust", "GCP", "Azure") if t.lower() not in owned), "Rust")
        n = sum(1 for m in self.messages(pc.id) if m.sender == "candidate")
        scenarios = [
            f"Thanks for reaching out. Before we talk, does this role actually use {known} day to day, "
            f"and is there any {unknown} on the team? I only move for the right stack.",
            f"Appreciate the note, but I only work with teams that are further along. "
            f"What stage are you at, and is {unknown} on the roadmap?",
            f"Sounds interesting, yes, I'd be open to a quick call this week. - {first}",
        ]
        return scenarios[n % len(scenarios)]

    def record_inbound(self, pc_id: str, text: str) -> None:
        pc = self.candidate(pc_id)
        if not pc:
            return
        self.add_message(Message(pipeline_id=pc_id, sender="candidate", language=pc.language, body=text))
        if pc.stage in (Stage.CONTACTED, Stage.SCREENED):
            self.set_stage(pc_id, Stage.REPLIED)

    def send_reply(self, pc_id: str, body: str, stage: str | None = None) -> dict | None:
        pc = self.candidate(pc_id)
        if not pc:
            return None
        self.add_message(Message(pipeline_id=pc_id, sender="karya", language="en", body=body))
        if stage:
            try:
                self.set_stage(pc_id, Stage(stage))
            except ValueError:
                pass
        return {"messages": [m.model_dump() for m in self.messages(pc_id)]}

    def simulate_reply(self, pc_id: str) -> dict | None:
        """A candidate replies. Advances the stage and drafts an acknowledgement."""
        pc = self.candidate(pc_id)
        if not pc:
            return None
        first = pc.name.split()[0]
        reply = {
            "en": f"Hi, thanks for reaching out - yes, I'd be open to a quick call. - {first}",
            "hi": f"नमस्ते, संपर्क करने के लिए धन्यवाद - हाँ, मैं बात करने के लिए तैयार हूँ। - {first}",
            "mr": f"नमस्कार, संपर्क केल्याबद्दल धन्यवाद - हो, मी बोलायला तयार आहे. - {first}",
            "te": f"నమస్కారం, సంప్రదించినందుకు ధన్యవాదాలు - అవును, మాట్లాడటానికి సిద్ధంగా ఉన్నాను. - {first}",
        }.get(pc.language, "Thanks, happy to talk.")
        self.add_message(Message(pipeline_id=pc_id, sender="candidate", language=pc.language, body=reply))
        ack = f"Great to hear, {first}. Sharing a couple of slots shortly - looking forward to it."
        self.add_message(Message(pipeline_id=pc_id, sender="karya", language="en", body=ack))
        if pc.stage in (Stage.CONTACTED, Stage.SCREENED):
            self.set_stage(pc_id, Stage.REPLIED)
        return {"messages": [m.model_dump() for m in self.messages(pc_id)]}

    # ----- run ingestion -----

    def ingest_run(
        self,
        role_id: str,
        run_id: str,
        *,
        user_id: str,
        goal: str,
        report: dict,
        candidates: list[dict],
        drafts: list[dict],
    ) -> None:
        sent_ids = {d["candidate_id"] for d in drafts if d.get("sent")}
        draft_by_id = {d["candidate_id"]: d for d in drafts}
        now = time.time()

        for c in candidates:
            cid = c["candidate_id"]
            if c["verdict"] == "reject":
                stage = Stage.REJECTED
            elif cid in sent_ids:
                stage = Stage.CONTACTED
            else:
                stage = Stage.SCREENED
            pc = PipelineCandidate(
                user_id=user_id, role_id=role_id, candidate_id=cid, name=c["name"], language=c["language"],
                location=c.get("location", ""), fit=c["fit_score"], verdict=c["verdict"],
                stage=stage, claims=c["claims"], run_id=run_id, created_at=now, updated_at=now,
            )
            pc_id = self._upsert_pc(pc)
            if cid in sent_ids and cid in draft_by_id:
                d = draft_by_id[cid]
                body = f"{d.get('subject','')}\n\n{d.get('body','')}".strip()
                # Re-running must not repost outreach already in the thread.
                if not any(m.sender == "karya" and m.body == body for m in self.messages(pc_id)):
                    self.add_message(Message(
                        pipeline_id=pc_id, sender="karya", language=d.get("language", "en"),
                        body=body, created_at=now,
                    ))

        cost = report.get("cost", {})
        cmp = report.get("cost_comparison", {})
        rec = RunRecord(
            id=run_id, user_id=user_id, role_id=role_id, goal=goal, status="done",
            sourced=report.get("sourced", 0), screened=report.get("screened", 0), sent=report.get("sent", 0),
            cost_usd=cmp.get("karya_usd", cost.get("total_usd", 0.0)),
            frontier_only_usd=cmp.get("frontier_only_usd", 0.0), savings_x=cmp.get("savings_x"),
            claims_verified=report.get("claims", {}).get("verified", 0),
            claims_rejected=report.get("claims", {}).get("rejected", 0),
            by_tier=cost, created_at=now,
        )
        self.db.execute(
            "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rec.id, rec.user_id, rec.role_id, rec.goal, rec.status, rec.sourced, rec.screened, rec.sent,
                rec.cost_usd, rec.frontier_only_usd, rec.savings_x, rec.claims_verified,
                rec.claims_rejected, json.dumps(rec.by_tier), rec.created_at,
            ),
        )

    def runs(self, role_id: str | None = None, user_id: str | None = None) -> list[dict]:
        if role_id:
            rows = self.db.query("SELECT * FROM runs WHERE role_id=? ORDER BY created_at DESC", (role_id,))
        elif user_id:
            rows = self.db.query("SELECT * FROM runs WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        else:
            rows = self.db.query("SELECT * FROM runs ORDER BY created_at DESC")
        return [dict(r) for r in rows]

    # ----- dashboard -----

    def dashboard(self, user_id: str) -> dict[str, Any]:
        roles = self.roles(user_id)
        pcs = [self._pc(r) for r in self.db.query("SELECT * FROM pipeline WHERE user_id=?", (user_id,))]
        runs = self.runs(user_id=user_id)

        role_skill = {r.id: r.skill for r in roles}
        by_skill: dict[str, dict] = {}
        for r in roles:
            by_skill.setdefault(r.skill, {"roles": 0, "pipeline": 0, "contacted": 0})["roles"] += 1

        funnel = {s.value: 0 for s in FUNNEL}
        funnel[Stage.REJECTED.value] = 0
        lang_mix: dict[str, int] = {}
        advanced = {Stage.CONTACTED, Stage.REPLIED, Stage.INTERVIEW, Stage.OFFER}
        for pc in pcs:
            funnel[pc.stage.value] = funnel.get(pc.stage.value, 0) + 1
            lang_mix[pc.language] = lang_mix.get(pc.language, 0) + 1
            b = by_skill.setdefault(role_skill.get(pc.role_id, "hiring"), {"roles": 0, "pipeline": 0, "contacted": 0})
            b["pipeline"] += 1
            if pc.stage in advanced:
                b["contacted"] += 1

        tier_calls: dict[str, int] = {}
        karya_cost = frontier_cost = 0.0
        verified = rejected = sourced = sent = 0
        for r in runs:
            karya_cost += r["cost_usd"] or 0
            frontier_cost += r["frontier_only_usd"] or 0
            verified += r["claims_verified"] or 0
            rejected += r["claims_rejected"] or 0
            sourced += r["sourced"] or 0
            sent += r["sent"] or 0
            calls = _loads(r["by_tier"], {}).get("calls_by_tier", {})
            for k, v in calls.items():
                tier_calls[k] = tier_calls.get(k, 0) + v

        screened_total = sum(1 for pc in pcs if pc.stage != Stage.SOURCED)
        minutes = sourced * MIN_PER_SOURCED + screened_total * MIN_PER_SCREENED + sent * MIN_PER_OUTREACH

        return {
            "roles": {"total": len(roles), "open": sum(1 for r in roles if r.status == RoleStatus.OPEN)},
            "pipeline": {"total": len(pcs), "funnel": funnel},
            "runs": len(runs),
            "outreach_sent": sent,
            "candidates_sourced": sourced,
            "claims": {"verified": verified, "rejected": rejected},
            "cost": {
                "karya_usd": round(karya_cost, 4),
                "frontier_only_usd": round(frontier_cost, 4),
                "saved_usd": round(frontier_cost - karya_cost, 4),
                "savings_x": round(frontier_cost / karya_cost, 1) if karya_cost else None,
            },
            "tier_calls": tier_calls,
            "language_mix": lang_mix,
            "hours_saved": round(minutes / 60, 1),
            "by_skill": by_skill,
        }
