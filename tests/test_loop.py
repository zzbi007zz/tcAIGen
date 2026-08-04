from apps.api.models import (
    GateResult, LoopBudget, TestCaseSet, VerifierVerdict,
)
from apps.api.pipeline.loop import Loop, JUDGE_CONFIDENCE_THRESHOLD


def passing_verdict(confidence=0.95):
    return VerifierVerdict(passed=True, confidence=confidence)


def failing_verdict():
    return VerifierVerdict(passed=False, confidence=0.9, feedback="fix it")


def make_loop(sample_test_case_set, verdicts=None, budget=None):
    gen_calls = {"n": 0}

    def generator(reqs):
        gen_calls["n"] += 1
        return sample_test_case_set

    verdict_iter = iter(verdicts or [passing_verdict()])

    def verifier(tcs, source):
        return next(verdict_iter, passing_verdict())

    loop = Loop(budget=budget or LoopBudget(), generator=generator, verifier=verifier)
    return loop, gen_calls


def test_loop_passes_on_first_attempt(sample_test_case_set, sample_requirements_doc):
    loop, gen_calls = make_loop(sample_test_case_set)
    result = loop.run(sample_requirements_doc)
    assert result.passed and result.actual_iterations == 1 and gen_calls["n"] == 1


def test_loop_respects_max_iterations(sample_test_case_set, sample_requirements_doc):
    loop, gen_calls = make_loop(
        sample_test_case_set, verdicts=[failing_verdict()] * 5)
    result = loop.run(sample_requirements_doc)
    assert not result.passed
    assert result.actual_iterations <= loop.budget.max_iterations


def test_loop_tracks_budget(sample_test_case_set, sample_requirements_doc):
    budget = LoopBudget(max_iterations=3, max_usd=0.02, cost_per_iteration=0.03)
    loop, _ = make_loop(sample_test_case_set, verdicts=[failing_verdict()] * 5, budget=budget)
    result = loop.run(sample_requirements_doc)
    assert result.actual_iterations == 0  # budget exhausted before first iteration


def test_low_confidence_escalates_to_judge(sample_test_case_set, sample_requirements_doc):
    judge_calls = {"n": 0}

    def judge(tcs, source):
        judge_calls["n"] += 1
        return VerifierVerdict(passed=True, confidence=1.0)

    loop, _ = make_loop(sample_test_case_set, verdicts=[passing_verdict(confidence=0.5)])
    loop._judge = judge
    result = loop.run(sample_requirements_doc)
    assert judge_calls["n"] == 1 and result.passed


def test_high_confidence_not_escalated(sample_test_case_set, sample_requirements_doc):
    judge_calls = {"n": 0}

    def judge(tcs, source):
        judge_calls["n"] += 1
        return VerifierVerdict(passed=True)

    loop, _ = make_loop(sample_test_case_set, verdicts=[passing_verdict(confidence=0.95)])
    loop._judge = judge
    loop.run(sample_requirements_doc)
    assert judge_calls["n"] == 0


def test_low_confidence_threshold():
    assert 0.5 < JUDGE_CONFIDENCE_THRESHOLD <= 0.95


def test_no_progress_detector(sample_test_case_set):
    from apps.api.evals.metrics import gate
    g1 = gate(sample_test_case_set)
    g2 = gate(sample_test_case_set)
    from apps.api.pipeline.loop import _signature
    assert _signature(g1.errors) == _signature(g2.errors)


def test_no_progress_different_failures(sample_test_case_set):
    from apps.api.pipeline.loop import _signature
    assert _signature(["a", "b"]) != _signature(["a", "c"])


def test_gate_result_model():
    g = GateResult(passed=False, gherkin_pass=False, dup_count=2)
    assert g.dup_count == 2
