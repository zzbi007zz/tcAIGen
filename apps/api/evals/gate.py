"""Deterministic zero-token gate: Gherkin parse + text duplication."""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, List, Tuple

from apps.api.models import GateResult, TestCase, TestCaseSet
from apps.api.pipeline.generate import validate_gherkin


def _similarity(a: TestCase, b: TestCase) -> float:
    ta = " ".join(s.text for s in a.gherkin.steps)
    tb = " ".join(s.text for s in b.gherkin.steps)
    return SequenceMatcher(None, ta.lower(), tb.lower()).ratio()


def detect_duplicates(test_cases: TestCaseSet, threshold: float = 0.92) -> List[Tuple[str, str]]:
    """Detect duplicate test cases within each feature only.

    Cross-feature comparisons are excluded — tests from different features
    share domain vocabulary but test different behaviors.
    """
    pairs: List[Tuple[str, str]] = []
    cases = test_cases.test_cases
    # Group by feature_id
    by_feature: Dict[str, List[Tuple[int, TestCase]]] = {}
    for idx, tc in enumerate(cases):
        by_feature.setdefault(tc.feature_id, []).append((idx, tc))
    for feature_cases in by_feature.values():
        for i in range(len(feature_cases)):
            for j in range(i + 1, len(feature_cases)):
                if _similarity(feature_cases[i][1], feature_cases[j][1]) > threshold:
                    pairs.append((feature_cases[i][1].tc_id, feature_cases[j][1].tc_id))
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
