"""Calibration of metrics against a hand-labeled bad-case subset."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from apps.api.evals.metrics import gate
from apps.api.models import TestCaseSet

DATASET_PATH = Path(__file__).resolve().parent / "datasets" / "labeled_bad.json"


def load_labeled_set(path: Path = DATASET_PATH) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_kappa(human_labels: List[bool], metric_labels: List[bool]) -> float:
    """Cohen's kappa between human 'is_bad' labels and gate 'is_bad' verdicts."""
    if len(human_labels) != len(metric_labels) or not human_labels:
        raise ValueError("Label lists must be non-empty and equal length")
    n = len(human_labels)
    observed = sum(1 for h, m in zip(human_labels, metric_labels) if h == m) / n
    p_human = sum(human_labels) / n
    p_metric = sum(metric_labels) / n
    expected = p_human * p_metric + (1 - p_human) * (1 - p_metric)
    if expected == 1.0:
        return 1.0
    return (observed - expected) / (1 - expected)


def run_calibration(path: Path = DATASET_PATH) -> Dict[str, Any]:
    entries = load_labeled_set(path)
    human_labels: List[bool] = []
    metric_labels: List[bool] = []
    for entry in entries:
        human_labels.append(bool(entry["is_bad"]))
        tcs = TestCaseSet.model_validate({"test_cases": [entry["test_case"]]})
        metric_labels.append(not gate(tcs).passed)
    return {
        "n": len(entries),
        "kappa": compute_kappa(human_labels, metric_labels),
        "human_bad": sum(human_labels),
        "metric_bad": sum(metric_labels),
    }
