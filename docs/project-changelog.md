# Project Changelog

## 2026-08-05 — Quality Report v2: SBERT consistency, proxy-mutation, raw-source generation

### Added
- SBERT semantic metrics (`evals/semantic.py`, all-MiniLM-L6-v2, lazy singleton, local, zero API cost):
  - `compute_semantic_consistency()` — per-TC cosine similarity vs cited acceptance criterion
  - `compute_semantic_faithfulness()` — grounding_source vs source doc chunks
  - `detect_semantic_duplicates()` — paraphrase dedup at >= 0.95 title similarity
- Proxy-mutation score (`evals/proxy_mutation.py`, `prompts/proxy_mutation_v1.md`):
  LLM judges which bugs each test would catch/miss; samples max 5 TCs;
  degrades to 1.0 without API key, 0.5 per TC on LLM errors
- Generation prompt now includes raw source document alongside structured
  requirements JSON (`{source_document}` placeholder in `generation_v1.md`);
  `run_generation(source_text=...)`, loop and CLI pass parsed source through
- 15 new tests: semantic consistency/faithfulness/dedup, proxy-mutation
  degrade paths, source injection, v2 breakdown keys

### Changed
- Faithfulness is now blended: 50% lexical token overlap + 50% SBERT semantic
- Overall score weights: 0.20 coverage + 0.15 balance + 0.15 faithfulness
  + 0.15 semantic consistency + 0.15 gherkin + 0.10 (1 - inferred ratio)
  + 0.10 proxy-mutation; -2 pts per duplicate (text OR semantic)
- `gate()`/`detect_duplicates()` extracted to `evals/gate.py` (re-exported
  from `metrics.py` for backward compatibility)
- Semantic consistency thresholds calibrated on golden dataset with
  all-MiniLM-L6-v2: warn < 0.35, critical < 0.20 (good pairs score
  0.26-0.85, unrelated pairs < 0.10)
- SBERT and proxy-mutation are skipped under pytest by default for speed;
  enable with `SBERT_TESTS=1` / explicit client

### Calibration results
- Golden dataset: 98.1/100 with new weights (no regression, gate >= 70)
- Labeled bad cases: 56.9-71.9; control good case: 84.5 — clear differentiation

### Tests
- 147 tests passing (132 existing + 15 new)

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
