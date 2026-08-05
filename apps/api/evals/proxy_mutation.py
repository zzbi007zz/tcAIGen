"""Proxy-mutation score: LLM-judged bug-catching effectiveness.

BDD/Gherkin tests lack executable code, so a real mutation score is
impossible. Instead, ask the LLM which bugs each test would catch/miss
and score the ratio. Degrades gracefully: no API key -> 1.0 (no penalty),
LLM error -> neutral 0.5 per test case.
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import List, Optional

from apps.api.models import TestCaseSet
from apps.api.pipeline.extract import strip_markdown_fences
from apps.api.pipeline.export.gherkin_writer import format_gherkin
from apps.api.pipeline.gemini_client import GeminiClient, get_client

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
MAX_SAMPLE = 5
NEUTRAL_SCORE = 0.5

logger = logging.getLogger(__name__)


def load_proxy_mutation_prompt(version: str = "v1") -> str:
    path = PROMPTS_DIR / f"proxy_mutation_{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def _score_test_case(client: GeminiClient, gherkin_text: str, prompt: str) -> float:
    raw = client.generate_content(prompt.replace("{gherkin_text}", gherkin_text))
    result = json.loads(strip_markdown_fences(raw))
    caught_raw = result.get("bugs_caught")
    missed_raw = result.get("bugs_missed")
    caught = len(caught_raw) if isinstance(caught_raw, list) else 0
    missed = len(missed_raw) if isinstance(missed_raw, list) else 0
    if caught + missed == 0:
        return NEUTRAL_SCORE
    return caught / (caught + missed)


def compute_proxy_mutation(
    test_cases: TestCaseSet,
    client: Optional[GeminiClient] = None,
    max_samples: int = MAX_SAMPLE,
    seed: int = 42,
) -> float:
    """Ratio of bugs caught vs total across a sample of test cases (0.0-1.0)."""
    if not test_cases.test_cases:
        return 1.0
    client = client or get_client()
    if not client.available:
        return 1.0
    prompt = load_proxy_mutation_prompt()
    cases = list(test_cases.test_cases)
    if len(cases) > max_samples:
        cases = random.Random(seed).sample(cases, max_samples)
    cases = cases[:max_samples]
    scores: List[float] = []
    for tc in cases:
        try:
            scores.append(_score_test_case(client, format_gherkin(tc.gherkin), prompt))
        except Exception as exc:
            logger.warning("proxy-mutation failed for %s: %s", tc.tc_id, exc)
            scores.append(NEUTRAL_SCORE)
    return sum(scores) / len(scores) if scores else 1.0
