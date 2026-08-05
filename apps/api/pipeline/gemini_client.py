"""Gemini API wrapper with retry and graceful no-key handling."""
from __future__ import annotations

import os
import time
from typing import Any, Optional

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_ATTEMPTS = 3


class GeminiUnavailableError(RuntimeError):
    pass


class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
        max_attempts: int = MAX_ATTEMPTS,
    ) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.max_attempts = max_attempts
        self._client: Any = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self) -> Any:
        if not self.api_key:
            raise GeminiUnavailableError("GEMINI_API_KEY is not configured")
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_content(self, prompt: str, image: Any = None) -> str:
        client = self._get_client()
        contents: Any = [prompt, image] if image is not None else prompt
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=contents,
                )
                return response.text or ""
            except Exception as exc:  # retry on transient/rate-limit errors
                last_error = exc
                if attempt < self.max_attempts:
                    time.sleep(min(2 ** attempt, 8))
        raise GeminiUnavailableError(f"Gemini call failed: {last_error}")


def get_client(**kwargs: Any) -> GeminiClient:
    return GeminiClient(**kwargs)
