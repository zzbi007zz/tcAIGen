"""Deterministic zero-token gate: Gherkin parse + text duplication."""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import List, Tuple

from apps.api.models import GateResult, TestCase, TestCaseSet
from apps.api.pipeline.generate import validate_gherkin


def _similarity(a: TestCase, b: TestCase) -> float:
    ta = f"{a.title} {a.gherkin.title} {' '.join(s.text for s in a.gherkin.steps)}"
    tb = f"{b.title} {b.gherkin.title} {' '.join(s.text for s in b.gherkin.steps)}"
    return SequenceMatcher(None, ta.lower(), tb.lower()).ratio()


def detect_duplicates(test_cases: TestCaseSet, threshold: float = 0.92) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    cases = test_cases.test_cases
    for i in range(len(cases)):
        for j in range(i + 1, len(cases)):
            if _similarity(cases[i], cases[j]) > threshold:
                pairs.append((cases[i].tc_id, cases[j].tc_id))
    return pairs


def gate(test_cases: TestCaseSet) -> GateResult:
    bad_gherkin = validate_gherkin(test_cases)
    dup_pairs = detect_duplicates(test_cases)
    errors = [f"Invalid Gherkin in {tc_id}" for tc_id in bad_gherkin]
    errors += [f"Duplicate pair {a}/{b}" for a, b in dup_pairs]
    return GateResult(
        passed=not bad_gherkin and not dup_pairs,
        gherkin_pass=not bad_gherkin,
        dup_count=len(dup_pairs),
        errors=errors,
    )
