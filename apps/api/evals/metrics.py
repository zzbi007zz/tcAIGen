"""Quality metrics + deterministic gate for generated test cases."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from apps.api.models import GateResult, RequirementsDocument, TestCase, TestCaseSet
from apps.api.pipeline.generate import validate_gherkin


class MetricWarning(BaseModel):
    metric: str
    message: str
    tc_ids: List[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    overall_score: float
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[MetricWarning] = Field(default_factory=list)


def compute_ac_coverage(
    test_cases: TestCaseSet, requirements: RequirementsDocument
) -> Tuple[float, List[str]]:
    total, covered, uncovered = 0, 0, []
    tc_text = " ".join(
        f"{tc.title} {tc.grounding_source} {tc.gherkin.title}".lower()
        for tc in test_cases.test_cases
    )
    for feature in requirements.features:
        for ac in feature.acceptance_criteria:
            total += 1
            keywords = {w for w in re.findall(r"[a-z0-9]+", ac.text.lower()) if len(w) > 3}
            if keywords and any(k in tc_text for k in keywords):
                covered += 1
            else:
                uncovered.append(ac.id)
    return (covered / total if total else 1.0), uncovered


def compute_category_balance(test_cases: TestCaseSet) -> Dict[str, float]:
    counts: Dict[str, int] = {"positive": 0, "negative": 0, "edge": 0, "boundary": 0}
    for tc in test_cases.test_cases:
        counts[tc.category.value] = counts.get(tc.category.value, 0) + 1
    total = sum(counts.values()) or 1
    return {k: v / total for k, v in counts.items()}


def compute_faithfulness(
    test_cases: TestCaseSet, source_doc: str = ""
) -> float:
    """Lexical overlap of grounding_source with the source document (G-Eval fallback)."""
    if not test_cases.test_cases:
        return 1.0
    source_tokens = set(re.findall(r"[a-z0-9]+", source_doc.lower())) if source_doc else None
    scores: List[float] = []
    for tc in test_cases.test_cases:
        grounding = tc.grounding_source.strip()
        if not grounding:
            scores.append(0.0)
        elif source_tokens is None:
            scores.append(1.0)
        else:
            grounding_tokens = set(re.findall(r"[a-z0-9]+", grounding.lower()))
            if not grounding_tokens:
                scores.append(0.0)
            else:
                scores.append(len(grounding_tokens & source_tokens) / len(grounding_tokens))
    return sum(scores) / len(scores)


def compute_inferred_ratio(
    test_cases: TestCaseSet, requirements: Optional[RequirementsDocument] = None
) -> float:
    if not test_cases.test_cases:
        return 0.0
    # Primary: count grounding_source containing "(inferred)" tag
    inferred = sum(1 for tc in test_cases.test_cases if "inferred" in tc.grounding_source.lower())
    if inferred > 0:
        return inferred / len(test_cases.test_cases)
    # Fallback: if no explicit tags but requirements has inferred ACs, use that ratio
    if requirements is not None:
        total_ac = sum(len(f.acceptance_criteria) for f in requirements.features)
        if total_ac > 0:
            inferred_ac = sum(
                1 for f in requirements.features
                for ac in f.acceptance_criteria
                if ac.grounding.value == "inferred"
            )
            return inferred_ac / total_ac
    return 0.0


def validate_gherkin_syntax(test_cases: TestCaseSet) -> List[str]:
    return validate_gherkin(test_cases)


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
    """Deterministic zero-token gate: gherkin parse + duplication."""
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


def evaluate_all(
    test_cases: TestCaseSet,
    requirements: Optional[RequirementsDocument] = None,
    source_doc: str = "",
) -> QualityReport:
    warnings: List[MetricWarning] = []
    breakdown: Dict[str, Any] = {}

    coverage, uncovered = 1.0, []
    if requirements is not None:
        coverage, uncovered = compute_ac_coverage(test_cases, requirements)
        if coverage < 0.85:
            warnings.append(MetricWarning(
                metric="ac_coverage",
                message=f"AC coverage {coverage:.0%} below 85%",
                tc_ids=uncovered,
            ))
    breakdown["ac_coverage"] = coverage

    balance = compute_category_balance(test_cases)
    breakdown["category_balance"] = balance
    if balance.get("negative", 0.0) < 0.20:
        warnings.append(MetricWarning(
            metric="category_balance",
            message=f"Negative ratio {balance.get('negative', 0):.0%} below 20%",
        ))

    faithfulness = compute_faithfulness(test_cases, source_doc)
    breakdown["faithfulness"] = faithfulness
    if faithfulness < 0.8:
        warnings.append(MetricWarning(
            metric="faithfulness", message=f"Faithfulness {faithfulness:.2f} below 0.8"
        ))

    breakdown["inferred_ratio"] = compute_inferred_ratio(test_cases, requirements)

    bad_gherkin = validate_gherkin_syntax(test_cases)
    breakdown["gherkin_validity"] = 1.0 if not bad_gherkin else 0.0
    if bad_gherkin:
        warnings.append(MetricWarning(
            metric="gherkin_validity",
            message="Unparseable Gherkin detected",
            tc_ids=bad_gherkin,
        ))

    dup_pairs = detect_duplicates(test_cases)
    breakdown["duplicates"] = [list(p) for p in dup_pairs]
    if dup_pairs:
        warnings.append(MetricWarning(
            metric="duplication",
            message=f"{len(dup_pairs)} duplicate pair(s) > 0.92 similarity",
            tc_ids=[tc for pair in dup_pairs for tc in pair],
        ))

    score = (
        0.30 * coverage
        + 0.20 * (1.0 if balance.get("negative", 0) >= 0.20 else balance.get("negative", 0) / 0.20)
        + 0.25 * faithfulness
        + 0.25 * breakdown["gherkin_validity"]
    ) * 100
    if dup_pairs:
        score -= min(10, 2 * len(dup_pairs))
    return QualityReport(
        overall_score=round(max(0.0, score), 1),
        breakdown=breakdown,
        warnings=warnings,
    )
