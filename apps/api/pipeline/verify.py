"""Cross-family verification: verify generator output with a different model family."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from apps.api.models import TestCaseSet, VerifierVerdict
from apps.api.pipeline.extract import strip_markdown_fences
from apps.api.pipeline.model_router import get_client

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class VerificationError(RuntimeError):
    pass


def load_verify_prompt() -> str:
    path = PROMPTS_DIR / "verify.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def build_verify_prompt(output: TestCaseSet, source: str) -> str:
    """Prompt contains ONLY output + source + rubric — never generator reasoning."""
    template = load_verify_prompt()
    return template.replace("{source}", source).replace(
        "{output}", output.model_dump_json(indent=2)
    )


def _verify_with_client(client: Any, prompt: str) -> VerifierVerdict:
    raw = client.generate_content(prompt)
    verdict = VerifierVerdict.model_validate(json.loads(strip_markdown_fences(raw)))
    verdict.model = getattr(client, "model", None)
    return verdict


def verify(
    test_cases: TestCaseSet,
    source: str,
    client: Optional[Any] = None,
    max_attempts: int = 2,
) -> VerifierVerdict:
    client = client or get_client("verify")
    if not getattr(client, "available", True):
        # Graceful degrade: no OpenRouter key -> skip verification
        return VerifierVerdict(
            passed=True, confidence=0.0,
            feedback="Verification skipped: verifier client unavailable",
        )
    prompt = build_verify_prompt(test_cases, source)
    last_error: Optional[Exception] = None
    for _ in range(max_attempts):
        try:
            return _verify_with_client(client, prompt)
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            prompt += f"\n\nPrevious verdict failed to parse: {exc}. Return valid JSON only."
    raise VerificationError(f"Verification failed: {last_error}")
