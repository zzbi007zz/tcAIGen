# BDD-First Test Case Generator

Generates Gherkin test cases from BA documents (txt/docx/pdf) + optional UI screenshots,
and proves output quality with a deterministic gate + 6-metric quality report.

**"The test case generator that proves its output quality."**

## Features

- **Multi-format ingestion** — txt, md, docx, pdf (up to 50MB)
- **Explicit/inferred tagging** — every requirement tagged for hallucination tracking
- **Vision + gap detection** — screenshot -> UI inventory -> feature-screen mapping -> 3 gap types
- **Gherkin-first output** — `Scenario Outline` + Examples tables, declarative steps, `grounding_source` on every case
- **Deterministic gate** — zero-token Gherkin parse + duplication check before LLM verification
- **Cross-family verification** — Gemini generates, Claude/GPT verifies via OpenRouter (optional)
- **Quality report** — 6 metrics with warnings: AC Coverage, Category Balance, Faithfulness, Inferred Ratio, Gherkin Validity, Duplication
- **Self-quality gate** — AI validates unique IDs, step-result 1:1 mapping, concrete data, field coverage, grounding before returning
- **Web UI** — drag-and-drop upload, pipeline progress, gap report, test case browser, quality dashboard, export
- **CLI + API** — headless mode for CI/CD, REST API for integrations

## Quick Start

```bash
# 1. Setup
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Edit .env: add GEMINI_API_KEY (required) and OPENROUTER_API_KEY (optional)

# 2. CLI demo
.venv/bin/python -m apps.cli run tests/fixtures/sample_ba_doc.txt --verbose --screenshots path/to/screenshots/
# Outputs .feature files + report.md into output/

# 3. API server
.venv/bin/uvicorn apps.api.server:app --reload --port 8001

# 4. Web UI
cd apps/web && npm install && npm run dev
# Open http://localhost:3000 (ensure API_BASE_URL points to your backend)
```

## Pipeline

```
BA Doc (.txt/.md/.docx/.pdf)
    │
    ├─── ingest ──→ raw text
    │
    ├─── extract (Gemini 2.5 Flash) ──→ RequirementsDocument
    │       └── explicit/inferred tagging on every acceptance criterion
    │
    ├─── vision (Gemini Vision) ──→ UIInventory
    │       └── visible elements only, no behavior inference
    │
    ├─── merge ──→ MergeResult (mappings + gaps)
    │       └── 3 gap types: requirement_without_design, design_without_requirement, validation_mismatch
    │
    └─── generate (Gemini 2.5 Flash) ──→ TestCaseSet
            │
            ├── gate() ──→ Gherkin parse + duplication check (FREE)
            │
            ├── verify (OpenRouter Claude/GPT) ──→ VerifierVerdict
            │       └── cross-family, no generator reasoning in prompt
            │
            └── loop (max 3 iterations, $0.50 budget) ──→ converge or exhaust
                    │
                    ├── export/ ──→ .feature files + .xlsx
                    └── metrics/ ──→ QualityReport (6 metrics)
```

## Quality Report Metrics

| Metric | Description | Warning Threshold |
|--------|-------------|-------------------|
| AC Coverage | % acceptance criteria with >= 1 test case | < 85% |
| Category Balance | positive : negative : edge : boundary ratio | negative < 20% |
| Faithfulness | token overlap between grounding_source and source doc | < 0.8 |
| Inferred Ratio | % test cases from inferred (vs explicit) criteria | informational |
| Gherkin Validity | % test cases with parseable Gherkin | any failure = hard gate |
| Duplication | pairs with > 92% text similarity | any detected |

Overall score weighted: 30% AC coverage + 20% category balance + 25% faithfulness + 25% gherkin validity, minus 2 points per duplicate pair (max -10).

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/extract` | POST | Upload BA doc → RequirementsDocument |
| `/vision` | POST | Upload screenshots → UIInventory |
| `/merge` | POST | Merge requirements + UI → MergeResult |
| `/generate` | POST | Full pipeline (doc + optional screenshots) → job_id |
| `/status/{job_id}` | GET | Poll job progress and results |
| `/export/{job_id}/gherkin` | GET | Download .feature files as zip |
| `/export/{job_id}/xlsx` | GET | Download .xlsx spreadsheet |
| `/prompts` | GET | List available prompt versions |

## Project Structure

```
apps/
├── api/
│   ├── models/        # Pydantic v2 schemas (requirements, UI, merge, test_case, verdict)
│   ├── pipeline/      # Core logic: ingest, extract, generate, vision, merge, verify, loop
│   │   └── export/    # .feature and .xlsx writers
│   ├── evals/         # 6 quality metrics, gate, calibration, golden dataset
│   │   └── datasets/  # labeled_bad.json + golden ground truth
│   ├── prompts/       # Versioned LLM prompts (extraction_v1, generation_v1, vision_v1, merge_v1, verify)
│   └── server.py      # FastAPI application
├── cli.py             # Headless CLI: python -m apps.cli run <doc>
└── web/               # Next.js 14 frontend
    └── src/
        ├── app/       # Layout + main pipeline page
        ├── components/ # FileUpload, PipelineProgress, GapReport, TestCaseBrowser,
        │               # QualityDashboard, ExportPanel
        └── lib/       # API client (fetch wrappers)
tests/                  # 132 pytest tests (unit + integration)
docs/                   # Architecture, code standards, PDR, changelog
plans/                  # Rebuild plan (9 phases) + research reports
```

## Tech Stack

- **Backend:** FastAPI + Pydantic v2 + google-genai + openai (OpenRouter)
- **Frontend:** Next.js 14 + React 18 + TypeScript
- **LLMs:** Gemini 2.5 Flash (generate/vision) + Claude/GPT via OpenRouter (verify/judge)
- **Testing:** pytest (132 tests, 0 failures)
- **CI:** GitHub Actions (pytest + coverage >= 80% + eval regression gate)

## Testing

```bash
.venv/bin/python -m pytest -p no:deepeval -p no:rerunfailures
```

132 tests across 14 test files. All tests use mocked LLM clients — no API keys required.
CI enforces >= 80% coverage on `apps/api/` and runs golden dataset regression on PRs.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for generation + vision |
| `OPENROUTER_API_KEY` | No | OpenRouter key for cross-family verify/judge. Without it, loop degrades to gate-only. |

## Documentation

- [System Architecture](docs/system-architecture.md)
- [Code Standards](docs/code-standards.md)
- [Project Overview (PDR)](docs/project-overview-pdr.md)
- [Changelog](docs/project-changelog.md)
