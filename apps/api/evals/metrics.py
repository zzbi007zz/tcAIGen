"""Quality metrics + quality report for generated test cases."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from apps.api.evals import proxy_mutation, semantic
from apps.api.evals.gate import detect_duplicates, gate  # re-export
from apps.api.models import RequirementsDocument, TestCaseSet
from apps.api.pipeline.gemini_client import GeminiClient
from apps.api.pipeline.generate import validate_gherkin

__all__ = [
    "MetricWarning",
    "QualityReport",
    "compute_ac_coverage",
    "compute_category_balance",
    "compute_faithfulness",
    "compute_inferred_ratio",
    "compute_outline_efficiency",
    "validate_gherkin_syntax",
    "evaluate_all",
    "detect_duplicates",
    "gate",
]

# Calibrated on golden dataset with all-MiniLM-L6-v2:
# good TC<->AC pairs score 0.26-0.85 (mean ~0.54), unrelated pairs < 0.10
SEMANTIC_CONSISTENCY_WARN = 0.35
SEMANTIC_CONSISTENCY_CRITICAL = 0.20
PROXY_MUTATION_WARN = 0.60


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
    """Blend 50% lexical token overlap + 50% SBERT semantic similarity.

    Falls back to pure lexical scoring when SBERT or the source doc is
    unavailable.
    """
    lexical = _compute_lexical_faithfulness(test_cases, source_doc)
    if os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("SBERT_TESTS"):
        return lexical
    semantic_score = semantic.compute_semantic_faithfulness(test_cases, source_doc)
    if semantic_score is None:
        return lexical
    return 0.5 * lexical + 0.5 * semantic_score


def _compute_lexical_faithfulness(
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


def compute_outline_efficiency(test_cases: TestCaseSet) -> float:
    """Ratio of test cases using scenario_outline vs total.

    Measures how well structurally similar scenarios are merged into
    Scenario Outline + Examples. 1.0 = all merged, 0.0 = all separate.
    """
    if not test_cases.test_cases:
        return 1.0
    outlines = sum(1 for tc in test_cases.test_cases
                   if tc.gherkin.scenario_type.value == "scenario_outline")
    return outlines / len(test_cases.test_cases)


def validate_gherkin_syntax(test_cases: TestCaseSet) -> List[str]:
    return validate_gherkin(test_cases)


def evaluate_all(
    test_cases: TestCaseSet,
    requirements: Optional[RequirementsDocument] = None,
    source_doc: str = "",
    client: Optional[GeminiClient] = None,
) -> QualityReport:
    warnings: List[MetricWarning] = []
    breakdown: Dict[str, Any] = {}
    sbert_enabled = not (
        os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("SBERT_TESTS")
    )

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
            metric="faithfulness", message=f"Faithfulness {faithfulness:.3f} below 0.80"
        ))

    inferred_ratio = compute_inferred_ratio(test_cases, requirements)
    breakdown["inferred_ratio"] = inferred_ratio

    consistency: Optional[float] = None
    if requirements is not None and sbert_enabled:
        consistency = semantic.compute_semantic_consistency(test_cases, requirements)
    breakdown["semantic_consistency"] = consistency
    if consistency is not None and consistency < SEMANTIC_CONSISTENCY_WARN:
        severity = "critically " if consistency < SEMANTIC_CONSISTENCY_CRITICAL else ""
        warnings.append(MetricWarning(
            metric="semantic_consistency",
            message=f"Semantic consistency {consistency:.2f} {severity}below "
                    f"{SEMANTIC_CONSISTENCY_WARN}",
        ))

    bad_gherkin = validate_gherkin_syntax(test_cases)
    gherkin_validity = 1.0 if not bad_gherkin else 0.0
    breakdown["gherkin_validity"] = gherkin_validity
    if bad_gherkin:
        warnings.append(MetricWarning(
            metric="gherkin_validity",
            message="Unparseable Gherkin detected",
            tc_ids=bad_gherkin,
        ))

    outline_eff = compute_outline_efficiency(test_cases)
    breakdown["outline_efficiency"] = outline_eff
    if outline_eff < 0.5:
        warnings.append(MetricWarning(
            metric="outline_efficiency",
            message=f"Only {outline_eff:.0%} of scenario_outline usage. "
                    f"Consider merging structurally similar scenarios.",
        ))

    proxy_enabled = client is not None or not (
        os.environ.get("PYTEST_CURRENT_TEST") and not os.environ.get("PROXY_TESTS")
    )
    mutation = (
        proxy_mutation.compute_proxy_mutation(test_cases, client)
        if proxy_enabled
        else 1.0
    )
    breakdown["proxy_mutation"] = mutation
    if mutation < PROXY_MUTATION_WARN:
        warnings.append(MetricWarning(
            metric="proxy_mutation",
            message=f"Proxy-mutation {mutation:.2f} below {PROXY_MUTATION_WARN}",
        ))

    score = (
        0.20 * coverage
        + 0.15 * (1.0 if balance.get("negative", 0) >= 0.20 else balance.get("negative", 0) / 0.20)
        + 0.15 * faithfulness
        + 0.15 * (consistency if consistency is not None else 1.0)
        + 0.15 * gherkin_validity
        + 0.10 * (1.0 - inferred_ratio)
        + 0.10 * mutation
    ) * 100
    return QualityReport(
        overall_score=round(max(0.0, score), 1),
        breakdown=breakdown,
        warnings=warnings,
    )
