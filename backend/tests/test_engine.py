from karya.core.models import ClaimStatus, GoalStatus
from karya.engine import KaryaEngine

from conftest import mock_settings, run_to_completion


async def test_full_run_completes_and_sends():
    engine = KaryaEngine(mock_settings())
    run_id = await run_to_completion(engine, "Hire 2 backend engineers in Pune", approve=True)
    ctx = engine.run_context(run_id)

    assert ctx.goal.status == GoalStatus.DONE
    assert ctx.job.location == "Pune" and ctx.job.headcount == 2
    assert len(ctx.finalists) == 2
    assert ctx.report["sent"] == 2
    assert ctx.report["claims"]["verified"] > 0
    assert ctx.report["cost"]["total_usd"] > 0


async def test_declining_approval_sends_nothing():
    engine = KaryaEngine(mock_settings())
    run_id = await run_to_completion(engine, "Hire 1 backend engineer in Pune", approve=False)
    ctx = engine.run_context(run_id)
    assert ctx.goal.status == GoalStatus.DONE
    assert ctx.report["sent"] == 0


async def test_no_claim_survives_without_evidence():
    engine = KaryaEngine(mock_settings())
    run_id = await run_to_completion(engine, "Hire 2 backend engineers in Pune")
    ctx = engine.run_context(run_id)
    for screening in ctx.screenings:
        for claim in screening.claims:
            if claim.status == ClaimStatus.VERIFIED:
                # every verified claim cites at least one real line
                assert claim.evidence_lines
                for n in claim.evidence_lines:
                    assert engine.state.evidence.get(claim.subject_id, n) is not None


async def test_savings_versus_frontier_only():
    engine = KaryaEngine(mock_settings())
    run_id = await run_to_completion(engine, "Hire 2 backend engineers in Pune")
    ctx = engine.run_context(run_id)
    comp = ctx.report["cost_comparison"]
    assert comp["frontier_only_usd"] > comp["karya_usd"]  # routing actually saves money


async def test_read_apis_expose_runs_talent_and_evidence():
    engine = KaryaEngine(mock_settings())
    run_id = await run_to_completion(engine, "Hire 2 backend engineers in Pune")

    runs = engine.list_runs()
    assert any(r["run_id"] == run_id for r in runs)

    talent = engine.talent()
    assert len(talent) > 5 and all("skills" in t for t in talent)

    detail = engine.run_candidates(run_id)
    assert detail and detail[0]["fit_score"] >= detail[-1]["fit_score"]  # sorted by fit
    # every cited evidence line resolves to real text
    for cand in detail:
        for claim in cand["claims"]:
            for ev in claim["evidence"]:
                assert ev["text"] != ""
