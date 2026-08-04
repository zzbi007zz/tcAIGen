import json
from pathlib import Path

import pytest

from apps.api.evals.metrics import evaluate_all
from apps.api.models import RequirementsDocument, TestCaseSet

GOLDEN = Path(__file__).resolve().parents[1] / "apps" / "api" / "evals" / "datasets" / "golden"
MIN_SCORE = 70.0


@pytest.fixture
def golden_set():
    return TestCaseSet.model_validate_json((GOLDEN / "ground_truth_tcs.json").read_text())


@pytest.fixture
def golden_doc():
    return (GOLDEN / "sample_ba_doc.md").read_text()


def test_golden_dataset_scores(golden_set, golden_doc):
    report = evaluate_all(golden_set, source_doc=golden_doc)
    assert report.overall_score >= MIN_SCORE


def test_golden_gherkin_all_valid(golden_set):
    from apps.api.evals.metrics import gate
    assert gate(golden_set).passed


def test_scores_within_threshold(golden_set, golden_doc):
    report = evaluate_all(golden_set, source_doc=golden_doc)
    assert report.breakdown["gherkin_validity"] == 1.0
    assert report.breakdown["faithfulness"] >= 0.5
