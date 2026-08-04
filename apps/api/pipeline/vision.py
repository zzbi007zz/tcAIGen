"""Vision pipeline: screenshots -> UIInventory via Gemini Vision."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from apps.api.models import UIInventory
from apps.api.pipeline.extract import strip_markdown_fences
from apps.api.pipeline.gemini_client import GeminiClient, GeminiUnavailableError, get_client

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
MIME_BY_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
MAX_SCREENSHOTS = 5


def load_vision_prompt(version: str = "v1") -> str:
    path = PROMPTS_DIR / f"vision_{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def mime_type_from_file(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext in MIME_BY_EXT:
        return MIME_BY_EXT[ext]
    raise ValueError(f"Unsupported image type: {ext}")


def analyze_screenshot(
    path: str | Path,
    client: Optional[GeminiClient] = None,
    prompt_version: str = "v1",
) -> UIInventory:
    client = client or get_client()
    if not client.available:
        raise GeminiUnavailableError("GEMINI_API_KEY is not configured")
    mime_type_from_file(path)  # validate extension
    prompt = load_vision_prompt(prompt_version)
    try:
        from google.genai import types

        image = types.Part.from_bytes(
            data=Path(path).read_bytes(), mime_type=mime_type_from_file(path)
        )
    except ImportError as exc:
        raise GeminiUnavailableError(f"google-genai not installed: {exc}") from exc
    raw = client.generate_content(prompt, image=image)
    return UIInventory.model_validate(json.loads(strip_markdown_fences(raw)))


def run_vision_pipeline(
    screenshot_paths: List[str | Path],
    client: Optional[GeminiClient] = None,
    prompt_version: str = "v1",
) -> UIInventory:
    if len(screenshot_paths) > MAX_SCREENSHOTS:
        raise ValueError(f"Max {MAX_SCREENSHOTS} screenshots per call")
    client = client or get_client()
    if not client.available:
        return UIInventory(screens=[])
    combined = UIInventory(screens=[])
    for path in screenshot_paths:
        inventory = analyze_screenshot(path, client=client, prompt_version=prompt_version)
        combined.screens.extend(inventory.screens)
    return combined
