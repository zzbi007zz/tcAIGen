# BDD-First Test Case Generator

Generates Gherkin test cases from BA documents (txt/docx/pdf) + optional Figma
screenshots, and proves output quality with a deterministic gate + metrics report.

**Positioning:** the test case generator that proves its output quality.

## Quick Start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # set GEMINI_API_KEY (and optionally OPENROUTER_API_KEY)
```

### CLI demo

```bash
.venv/bin/python -m apps.cli run tests/fixtures/sample_ba_doc.txt --verbose
```

Outputs `.feature` files + `report.md` (quality report) into `output/`.

### API server

```bash
.venv/bin/uvicorn apps.api.server:app --reload
```

Endpoints: `POST /extract`, `POST /vision`, `POST /merge`, `POST /generate`,
`GET /status/{job_id}`, `GET /export/{job_id}/gherkin|xlsx`, `GET /prompts`, `GET /health`.

### Web UI (Next.js)

```bash
cd apps/web && npm install && npm run dev
```

## Pipeline

```
BA Doc + Screenshots
  -> ingest -> extract (Gemini)        -> RequirementsDocument
  -> vision (Gemini Vision)            -> UIInventory
  -> merge                             -> MergeResult (gap report)
  -> generate (Gemini)                 -> TestCaseSet
  -> gate (deterministic, zero-token)  -> gherkin lint + dedup
  -> verify (OpenRouter, cross-family) -> VerifierVerdict
  -> loop (retry w/ feedback, max 3)   -> converge or exhaust budget
  -> export (.feature / .xlsx) + QualityReport
```

## Testing

```bash
.venv/bin/python -m pytest -p no:deepeval -p no:rerunfailures
```

132 tests: models, extraction, generation, gherkin writer, vision/merge,
eval metrics, gate, model router, verify, loop, server, CLI, eval regression.

Docs: `docs/system-architecture.md`, `docs/code-standards.md`,
`docs/project-overview-pdr.md`.
