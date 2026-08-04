"""Role-based cross-family LLM routing (generate/verify/judge)."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

ROLES: Dict[str, Dict[str, Any]] = {
    "generate": {
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "fallbacks": ["gemini-1.5-flash"],
    },
    "verify": {
        "provider": "openrouter",
        "model": "anthropic/claude-3.5-sonnet",
        "fallbacks": ["openai/gpt-4o-mini"],
    },
    "judge": {
        "provider": "openrouter",
        "model": "openai/gpt-4o",
        "fallbacks": ["qwen/qwen-2.5-72b-instruct"],
    },
}


class OpenRouterClient:
    """Minimal OpenRouter chat-completions client (OpenAI-compatible)."""

    def __init__(self, model: str, api_key: Optional[str] = None) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def generate_content(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""


def get_client(role: str) -> Any:
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")
    config = ROLES[role]
    if config["provider"] == "gemini":
        from apps.api.pipeline.gemini_client import get_client as get_gemini

        return get_gemini(model=config["model"])
    return OpenRouterClient(model=config["model"])


def get_fallback_models(role: str) -> list:
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")
    return ROLES[role]["fallbacks"]
