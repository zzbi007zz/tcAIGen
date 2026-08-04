"""Export TestCaseSet to an .xlsx workbook."""
from __future__ import annotations

from pathlib import Path

from apps.api.models import TestCaseSet

HEADERS = ["TC ID", "Feature", "Title", "Category", "Priority", "Grounding", "Gherkin"]


def _gherkin_text(tc) -> str:
    lines = [f"{tc.gherkin.scenario_type.value}: {tc.gherkin.title}"]
    lines += [f"{s.keyword} {s.text}" for s in tc.gherkin.steps]
    return "\n".join(lines)


def write_test_cases_xlsx(test_case_set: TestCaseSet, output_path: str | Path) -> Path:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Test Cases"
    ws.append(HEADERS)
    for tc in test_case_set.test_cases:
        ws.append([
            tc.tc_id, tc.feature_id, tc.title, tc.category.value,
            tc.priority, tc.grounding_source, _gherkin_text(tc),
        ])
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))
    return out
