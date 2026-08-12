"""Regressions for the workspace flow: what a user actually experiences when
they run a workspace, run it again, or write a spec the pool cannot serve."""

from karya.core.models import Job
from karya.engine import KaryaEngine
from karya.planes.execution.sandbox import _same_place
from karya.product.models import PipelineCandidate, Stage
from karya.product.store import ProductStore

from conftest import mock_settings, run_to_completion


def _job(**over) -> Job:
    spec = dict(
        id="job_test", title="Backend Engineer", location="Pune", headcount=2,
        must_have=["Python", "Kubernetes"], nice_to_have=["Go"], seniority="mid", pool="talent",
    )
    spec.update(over)
    return Job(**spec)


# ----- sourcing: a spec the pool cannot serve must say so -----


def test_sourcing_requires_a_real_skill_match():
    """Being in the right city is not a reason to source someone.

    A spec of skills nobody has used to return a full shortlist of locals, who
    were then screened, rejected, and reported as a successful run of nothing.
    """
    engine = KaryaEngine(mock_settings())
    job = _job(must_have=["Next Js", "Figma"], nice_to_have=[])
    found = engine.execution.sourcing.source("run_x", job, 8)
    assert found == []


def test_sourcing_still_finds_real_matches():
    engine = KaryaEngine(mock_settings())
    found = engine.execution.sourcing.source("run_x", _job(), 8)
    assert len(found) > 0
    wanted = {"python", "kubernetes", "go"}
    for c in found:
        assert {s.lower() for s in c.skills} & wanted


def test_out_of_town_matches_still_source():
    """Location ranks, it does not gate: a strong match elsewhere still shows up."""
    engine = KaryaEngine(mock_settings())
    found = engine.execution.sourcing.source("run_x", _job(location="Atlantis"), 8)
    assert len(found) > 0


def test_city_aliases_match():
    assert _same_place("Bengaluru", "Bangalore")
    assert _same_place("bangalore", "Bengaluru")
    assert not _same_place("Pune", "Mumbai")


async def test_no_match_run_explains_itself():
    engine = KaryaEngine(mock_settings())
    job = _job(must_have=["Next Js", "Figma"], nice_to_have=[])
    goal = engine.start_goal_for_job("Hire 2 Frontend Developers in Pune", job)
    await engine.task(goal.id)

    report = engine.run_context(goal.id).report
    note = report["no_match"]
    assert note is not None
    assert note["requested"] == ["Next Js", "Figma"]
    assert note["pool_size"] > 0
    # tells the user what the pool could actually match instead
    assert "Python" in note["available_skills"]


async def test_no_match_run_quotes_no_savings():
    """A run that made no model calls has no economics to report."""
    engine = KaryaEngine(mock_settings())
    job = _job(must_have=["Next Js", "Figma"], nice_to_have=[])
    goal = engine.start_goal_for_job("Hire 2 Frontend Developers in Pune", job)
    await engine.task(goal.id)

    comp = engine.run_context(goal.id).report["cost_comparison"]
    assert comp["karya_usd"] == 0
    assert comp["savings_x"] is None
    assert comp["frontier_only_usd"] is None


# ----- cost is per run, not cumulative -----


async def test_each_run_reports_only_its_own_cost():
    """One shared tally made every run report the sum of all runs before it."""
    engine = KaryaEngine(mock_settings())
    first = await run_to_completion(engine, "Hire 2 backend engineers in Pune")
    second = await run_to_completion(engine, "Hire 2 backend engineers in Pune")

    a = engine.run_context(first).report["cost"]["total_usd"]
    b = engine.run_context(second).report["cost"]["total_usd"]
    assert a > 0 and b > 0
    # the second run must not carry the first run's spend
    assert b < a * 1.5
    # while the process lifetime total does accumulate
    assert engine.state.ledger.snapshot()["total_usd"] > a


# ----- pipeline: re-running a workspace must not duplicate people -----


def _pc(role_id: str, cid: str, stage: Stage, **over) -> PipelineCandidate:
    spec = dict(
        user_id="usr_1", role_id=role_id, candidate_id=cid, name="Arya Kulkarni",
        language="en", location="Pune", fit=0.9, verdict="advance", stage=stage,
        claims=[], run_id="run_1",
    )
    spec.update(over)
    return PipelineCandidate(**spec)


def test_rerun_updates_instead_of_duplicating(tmp_path):
    store = ProductStore(tmp_path / "t.db")
    store._upsert_pc(_pc("ws_1", "cand_a", Stage.SCREENED))
    store._upsert_pc(_pc("ws_1", "cand_a", Stage.SCREENED, fit=0.95))

    pipe = store.pipeline("ws_1")
    assert len(pipe) == 1
    assert pipe[0].fit == 0.95  # refreshed, not duplicated


def test_rerun_keeps_human_progress(tmp_path):
    """A fresh run must not drag someone already at Interview back to Screened."""
    store = ProductStore(tmp_path / "t.db")
    store._upsert_pc(_pc("ws_1", "cand_a", Stage.SCREENED))
    pc_id = store.pipeline("ws_1")[0].id
    store.set_stage(pc_id, Stage.INTERVIEW)
    store.add_note(pc_id, "strong on system design")

    store._upsert_pc(_pc("ws_1", "cand_a", Stage.SCREENED))

    pipe = store.pipeline("ws_1")
    assert len(pipe) == 1
    assert pipe[0].stage == Stage.INTERVIEW
    assert len(pipe[0].notes) == 1  # the human's own work survives


def test_rerun_can_still_reject(tmp_path):
    store = ProductStore(tmp_path / "t.db")
    store._upsert_pc(_pc("ws_1", "cand_a", Stage.CONTACTED))
    store._upsert_pc(_pc("ws_1", "cand_a", Stage.REJECTED, verdict="reject"))
    assert store.pipeline("ws_1")[0].stage == Stage.REJECTED


def test_separate_workspaces_track_the_same_person(tmp_path):
    store = ProductStore(tmp_path / "t.db")
    store._upsert_pc(_pc("ws_1", "cand_a", Stage.SCREENED))
    store._upsert_pc(_pc("ws_2", "cand_a", Stage.SCREENED))
    assert len(store.pipeline("ws_1")) == 1
    assert len(store.pipeline("ws_2")) == 1
