"""Requirements extraction pipeline (LLM pass 1)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from apps.api.models import RequirementsDocument, SourceType
from apps.api.pipeline import ingest
from apps.api.pipeline.gemini_client import GeminiClient, get_client

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(version: str = "v1") -> str:
    path = PROMPTS_DIR / f"extraction_{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def fill_template(prompt: str, document_text: str) -> str:
    return prompt.replace("{document_text}", document_text)


def strip_markdown_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.lstrip("#").strip()
    return "Untitled Document"


def _parse_requirements(raw_json: str, source_type: str) -> RequirementsDocument:
    data: dict[str, Any] = json.loads(strip_markdown_fences(raw_json))
    return RequirementsDocument.model_validate(data)


def run_extraction(
    file_path: str | Path,
    client: Optional[GeminiClient] = None,
    prompt_version: str = "v1",
    max_attempts: int = 3,
) -> RequirementsDocument:
    text = ingest.parse_document(file_path)
    source_type = ingest.source_type_for(file_path)
    prompt = fill_template(load_prompt(prompt_version), text)
    client = client or get_client()
    if not client.available:
        raise GeminiUnavailableError("GEMINI_API_KEY is not configured")

    last_error: Optional[Exception] = None
    for _ in range(max_attempts):
        try:
            raw = client.generate_content(prompt)
            doc = _parse_requirements(raw, source_type)
            doc.meta.source_type = SourceType(source_type)
            if not doc.meta.title:
                doc.meta.title = extract_title(text)
            return doc
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            prompt = f"{prompt}\n\nPrevious output failed to parse: {exc}. Return valid JSON only."
    raise ValueError(f"Extraction failed after {max_attempts} attempts: {last_error}")
