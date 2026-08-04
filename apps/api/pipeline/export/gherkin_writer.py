"""Export TestCaseSet to .feature files."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from apps.api.models import Gherkin, ScenarioType, TestCase, TestCaseSet


def format_step(step) -> str:
    return f"    {step.keyword} {step.text}"


def format_examples_table(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return ""
    columns = list(rows[0].keys())
    lines = ["    Examples:", "      | " + " | ".join(columns) + " |"]
    for row in rows:
        lines.append("      | " + " | ".join(row.get(c, "") for c in columns) + " |")
    return "\n".join(lines)


def format_gherkin(gherkin: Gherkin) -> str:
    lines: List[str] = []
    if gherkin.tags:
        lines.append("  " + " ".join(t if t.startswith("@") else f"@{t}" for t in gherkin.tags))
    keyword = "Scenario Outline" if gherkin.scenario_type == ScenarioType.scenario_outline else "Scenario"
    lines.append(f"  {keyword}: {gherkin.title}")
    lines.extend(format_step(s) for s in gherkin.steps)
    if gherkin.examples_table:
        lines.append(format_examples_table(gherkin.examples_table))
    return "\n".join(lines)


def render_feature(feature_name: str, test_cases: List[TestCase]) -> str:
    body = "\n\n".join(format_gherkin(tc.gherkin) for tc in test_cases)
    return f"Feature: {feature_name}\n\n{body}\n"


def _safe_filename(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "feature"


def write_feature_file(
    test_case_set: TestCaseSet,
    output_dir: str | Path,
    feature_names: Dict[str, str] | None = None,
) -> List[Path]:
    """Write one .feature file per feature_id. Returns written paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    by_feature: Dict[str, List[TestCase]] = {}
    for tc in test_case_set.test_cases:
        by_feature.setdefault(tc.feature_id, []).append(tc)
    written: List[Path] = []
    for feature_id, cases in by_feature.items():
        name = (feature_names or {}).get(feature_id, feature_id)
        path = out / f"{_safe_filename(feature_id)}.feature"
        path.write_text(render_feature(name, cases), encoding="utf-8")
        written.append(path)
    return written
