from __future__ import annotations

import re

from ...core.events import EventType
from ...core.ids import new_id
from ...core.models import Goal, Job, NodeType, Plan, PlanNode
from ..state.store import StatePlane

_CITIES = ["Pune", "Mumbai", "Bangalore", "Bengaluru", "Hyderabad", "Delhi", "Remote", "Chennai"]
_NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "a": 1, "an": 1}

# role -> (canonical title, must-have, nice-to-have)
_ROLES = {
    "backend": ("Backend Engineer", ["Python", "Kubernetes"], ["Go", "payments", "PostgreSQL"]),
    "frontend": ("Frontend Engineer", ["React", "TypeScript"], ["Node.js", "REST"]),
    "full-stack": ("Full-stack Engineer", ["Node.js", "React"], ["TypeScript", "MongoDB"]),
    "fullstack": ("Full-stack Engineer", ["Node.js", "React"], ["TypeScript", "MongoDB"]),
    "data": ("Data Engineer", ["Python", "Kafka"], ["AWS", "PostgreSQL"]),
}


class Planner:
    """Turns 'describe the outcome' into a concrete, ordered plan.

    Goal parsing is deterministic here; the model spend is reserved for the hard
    per-candidate work in the execution plane, where it actually moves accuracy.
    """

    def parse_goal(self, run_id: str, goal: Goal, state: StatePlane) -> Job:
        text = goal.text.lower()
        headcount = 1
        m = re.search(r"\b(\d+)\b", text)
        if m:
            headcount = int(m.group(1))
        else:
            for word, val in _NUM_WORDS.items():
                if re.search(rf"\b{word}\b", text):
                    headcount = val
                    break

        title, must, nice = _ROLES["backend"]
        for key, spec in _ROLES.items():
            if key in text:
                title, must, nice = spec
                break

        location = next((c for c in _CITIES if c.lower() in text), "Remote")
        if location == "Bengaluru":
            location = "Bangalore"

        return Job(
            id=new_id("job"),
            title=title,
            location=location,
            headcount=max(1, headcount),
            must_have=must,
            nice_to_have=nice,
            seniority="senior" if "senior" in text else "mid",
        )

    def plan(self, run_id: str, goal: Goal, job: Job, state: StatePlane) -> Plan:
        shortlist = max(job.headcount * 4, 6)
        nodes = [
            PlanNode(
                id="n_source",
                type=NodeType.SOURCE,
                title=f"Source ~{shortlist} {job.title}s in {job.location}",
                params={"limit": shortlist},
            ),
            PlanNode(
                id="n_screen",
                type=NodeType.SCREEN,
                title="Screen and ground every claim in evidence",
                depends_on=["n_source"],
            ),
            PlanNode(
                id="n_draft",
                type=NodeType.DRAFT_OUTREACH,
                title=f"Draft outreach for top {job.headcount} finalists",
                depends_on=["n_screen"],
                params={"finalists": job.headcount},
            ),
            PlanNode(
                id="n_send",
                type=NodeType.SEND_OUTREACH,
                title="Send outreach (needs your approval)",
                depends_on=["n_draft"],
            ),
            PlanNode(
                id="n_report",
                type=NodeType.REPORT,
                title="Compile the run report",
                depends_on=["n_send"],
            ),
        ]
        plan = Plan(goal_id=goal.id, nodes=nodes)
        state.entities.add_plan(plan)
        state.emit(
            run_id,
            EventType.PLAN_PRODUCED,
            f"decomposed goal into {len(nodes)}-node plan",
            {
                "job": job.model_dump(),
                "nodes": [{"id": n.id, "type": n.type.value, "depends_on": n.depends_on} for n in nodes],
            },
        )
        return plan
