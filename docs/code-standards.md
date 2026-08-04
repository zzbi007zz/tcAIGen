# Code Standards

## Principles
- YAGNI, KISS, DRY — no speculative features, simple solutions, no duplication.

## Structure
- Files under 200 lines; split into focused modules.
- kebab-case for docs; snake_case for Python; PascalCase React components.
- Models in `apps/api/models/`, business logic in `apps/api/pipeline/`,
  quality logic in `apps/api/evals/`.

## Python
- Pydantic v2 (`model_validate`, `model_dump_json`) — no v1 APIs.
- `from __future__ import annotations` in model files.
- LLM clients wrapped (`gemini_client`, `model_router`) — never call SDKs from
  business logic directly.
- All LLM calls mockable; tests never require API keys.
- Graceful degradation when `GEMINI_API_KEY` / `OPENROUTER_API_KEY` missing.

## Testing
- pytest; fixtures in `tests/fixtures/`, shared mocks in `tests/conftest.py`.
- No fake data to force passes; integration tests requiring keys must skip
  cleanly when keys are absent.
- Run: `pytest -p no:deepeval -p no:rerunfailures` (deepeval's pytest plugin
  opens sockets; disable in sandboxed environments).

## Commits
- Conventional commits (`feat:`, `fix:`, `test:`, `docs:`).
- No secrets (.env, API keys) in git.
