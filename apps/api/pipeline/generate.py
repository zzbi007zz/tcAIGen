"""Test case generation pipeline (LLM pass 2) + Gherkin validation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from apps.api.models import RequirementsDocument, TestCaseSet
from apps.api.pipeline.extract import strip_markdown_fences
from apps.api.pipeline.gemini_client import GeminiClient, get_client

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class GherkinValidationError(ValueError):
    pass


def load_generation_prompt(version: str = "v1") -> str:
    path = PROMPTS_DIR / f"generation_{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def build_feature_content(requirements_doc: RequirementsDocument) -> str:
    return requirements_doc.model_dump_json(indent=2)


def _parse_single(gherkin_text: str) -> bool:
    try:
        from gherkin.parser import Parser
        from gherkin.token_scanner import TokenScanner

        Parser().parse(TokenScanner(gherkin_text))
        return True
    except ImportError:
        return _regex_validate(gherkin_text)
    except Exception:
        return False


def _regex_validate(gherkin_text: str) -> bool:
    import re

    text = gherkin_text.strip()
    if not re.search(r"Scenario( Outline)?:", text):
        return False
    return bool(re.search(r"^\s*(Given|When|Then)\b", text, re.MULTILINE))


def validate_gherkin(test_cases: TestCaseSet) -> List[str]:
    """Return list of tc_ids whose Gherkin fails to parse."""
    from apps.api.pipeline.export.gherkin_writer import format_gherkin

    valid_keywords = {"Given", "When", "Then", "And", "But"}
    failures: List[str] = []
    for tc in test_cases.test_cases:
        g = tc.gherkin
        if (
            not g.title.strip()
            or not g.steps
            or any(step.keyword not in valid_keywords or not step.text.strip() for step in g.steps)
        ):
            failures.append(tc.tc_id)
            continue
        if not _parse_single("Feature: F\n" + format_gherkin(tc.gherkin)):
            failures.append(tc.tc_id)
    return failures


def validate_grounding(test_cases: TestCaseSet) -> List[str]:
    return [tc.tc_id for tc in test_cases.test_cases if not tc.grounding_source.strip()]


def run_generation(
    requirements_doc: RequirementsDocument,
    client: Optional[GeminiClient] = None,
    prompt_version: str = "v1",
    max_attempts: int = 3,
) -> TestCaseSet:
    prompt = load_generation_prompt(prompt_version).replace(
        "{requirements_json}", build_feature_content(requirements_doc)
    )
    client = client or get_client()
    last_error: Optional[Exception] = None
    for _ in range(max_attempts):
        try:
            raw = client.generate_content(prompt)
            test_cases = TestCaseSet.model_validate(json.loads(strip_markdown_fences(raw)))
            missing = validate_grounding(test_cases)
            if missing:
                raise ValueError(f"Missing grounding_source on: {missing}")
            bad_gherkin = validate_gherkin(test_cases)
            if bad_gherkin:
                raise GherkinValidationError(f"Invalid Gherkin in: {bad_gherkin}")
            return test_cases
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            prompt = f"{prompt}\n\nPrevious output was invalid: {exc}. Fix and return valid JSON only."
    raise ValueError(f"Generation failed after {max_attempts} attempts: {last_error}")
