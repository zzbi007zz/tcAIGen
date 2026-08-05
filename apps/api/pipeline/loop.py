"""Maker/verifier loop: generate -> gate -> verify -> judge -> retry."""
from __future__ import annotations

from typing import Any, Callable, List, Optional

from apps.api.evals.metrics import gate
from apps.api.models import (
    LoopBudget,
    LoopResult,
    RequirementsDocument,
    TestCaseSet,
    VerifierVerdict,
)
from apps.api.pipeline import generate, model_router, verify

JUDGE_CONFIDENCE_THRESHOLD = 0.7


def _signature(errors: List[str]) -> str:
    return "|".join(sorted(errors))


class Loop:
    def __init__(
        self,
        budget: Optional[LoopBudget] = None,
        generator: Optional[Callable[..., TestCaseSet]] = None,
        verifier: Optional[Callable[..., VerifierVerdict]] = None,
        judge: Optional[Callable[..., VerifierVerdict]] = None,
    ) -> None:
        self.budget = budget or LoopBudget()
        self._generator = generator or generate.run_generation
        self._verifier = verifier or verify.verify
        self._judge = judge

    def _call_judge(self, test_cases: TestCaseSet, source: str) -> VerifierVerdict:
        if self._judge is not None:
            return self._judge(test_cases, source)
        client = model_router.get_client("judge")
        return verify.verify(test_cases, source, client=client)

    def run(
        self,
        requirements: RequirementsDocument,
        source: str = "",
        feedback: Optional[str] = None,
    ) -> LoopResult:
        verdicts: List[VerifierVerdict] = []
        last_signature: Optional[str] = None
        total_cost = 0.0
        final_output: Optional[TestCaseSet] = None
        iterations = 0

        for iteration in range(1, self.budget.max_iterations + 1):
            if total_cost + self.budget.cost_per_iteration > self.budget.max_usd:
                break
            total_cost += self.budget.cost_per_iteration
            iterations = iteration

            test_cases = self._generator(requirements)
            final_output = test_cases

            gate_result = gate(test_cases)
            if gate_result.passed:
                try:
                    verdict = self._verifier(test_cases, source)
                except Exception as verr:
                    # Verifier unavailable (bad model name, network error, etc.)
                    # Skip verification and return generated output
                    verdicts.append(VerifierVerdict(
                        passed=False, confidence=0.0,
                        feedback=f"Verifier error: {verr}",
                    ))
                    return LoopResult(
                        passed=False,
                        actual_iterations=iteration,
                        total_cost=total_cost,
                        final_output=final_output.model_dump() if final_output else None,
                        verdicts=verdicts,
                    )
                verdicts.append(verdict)
                if verdict.passed:
                    if verdict.confidence < JUDGE_CONFIDENCE_THRESHOLD:
                        judge_verdict = self._call_judge(test_cases, source)
                        verdicts.append(judge_verdict)
                        return LoopResult(
                            passed=judge_verdict.passed,
                            actual_iterations=iteration,
                            total_cost=total_cost,
                            final_output=final_output.model_dump() if final_output else None,
                            verdicts=verdicts,
                        )
                    return LoopResult(
                        passed=True,
                        actual_iterations=iteration,
                        total_cost=total_cost,
                        final_output=final_output.model_dump() if final_output else None,
                        verdicts=verdicts,
                    )
                feedback = verdict.feedback
            else:
                signature = _signature(gate_result.errors)
                if (
                    self.budget.no_progress_stop
                    and signature == last_signature
                ):
                    break
                last_signature = signature
                feedback = "; ".join(gate_result.errors)

        return LoopResult(
            passed=False,
            actual_iterations=iterations,
            total_cost=total_cost,
            final_output=final_output.model_dump() if final_output else None,
            verdicts=verdicts,
        )


def run(requirements: RequirementsDocument, **kwargs: Any) -> LoopResult:
    return Loop(**{k: v for k, v in kwargs.items() if k in ("budget", "generator", "verifier", "judge")}).run(
        requirements, **{k: v for k, v in kwargs.items() if k not in ("budget", "generator", "verifier", "judge")}
    )
