# Project Changelog

## 2026-08-04 — BDD Test Case Generator full rebuild

### Added
- Pydantic schemas: requirements, ui_inventory, merge_gap, test_case, verdict (5 modules)
- Ingestion pipeline: txt/docx/pdf parsing (`ingest.py`)
- Extraction pipeline: Gemini pass 1 with explicit/inferred tagging (`extract.py`, `prompts/extraction_v1.md`)
- Generation pipeline: Gherkin test cases with mandatory `grounding_source`, retry on invalid output (`generate.py`, `prompts/generation_v1.md`)
- Export: `.feature` writer and `.xlsx` writer (`pipeline/export/`)
- Vision pipeline: screenshot -> UIInventory, visible-elements-only, graceful no-key degrade (`vision.py`)
- Merge/gap detection: 3 gap types via token-overlap mapping (`merge.py`)
- Eval harness: AC coverage, category balance, faithfulness, inferred ratio, gherkin validity (hard gate), duplication; `gate()` + `evaluate_all()` (`evals/metrics.py`)
- Calibration: Cohen's kappa against `labeled_bad.json` (7 entries)
- Loop verifier: role-based model routing (generate=Gemini, verify=Claude, judge=GPT via OpenRouter), budget tracking, no-progress stop, low-confidence judge escalation
- FastAPI server: /extract /vision /merge /generate /status /export /prompts /health
- CLI demo: `python -m apps.cli run <doc> [--screenshots dir]`
- Next.js web UI: upload, pipeline progress, gap report (before TCs), TC browser, quality dashboard, export panel
- Golden dataset: auth-module BA doc + 21 hand-written ground-truth test cases
- CI: pytest + coverage gate + golden-dataset eval regression gate
- Docs: PDR, system architecture, code standards, README, .env.example

### Tests
- 132 tests passing (exceeds prior 104-test parity target)

### Fixes during implementation
- Gherkin validation hardened: rejects empty titles/steps and invalid step keywords (official parser accepts them)
- Loop budget: cost check now happens before charging an iteration
