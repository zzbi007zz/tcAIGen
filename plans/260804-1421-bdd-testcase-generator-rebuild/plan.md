---
title: "BDD-First Test Case Generator — Full Rebuild"
description: "Rebuild the AI test case generator from technical spec: schemas → extraction → generation → vision → merge → eval → loop verifier → server → web UI → golden dataset"
status: completed
priority: P1
effort: 40h
branch: main
tags: [backend, api, pipeline, llm, bdd, gherkin, deepeval, frontend]
blockedBy: []
blocks: []
created: 2026-08-04
---

# BDD-First Test Case Generator — Full Rebuild

## Overview

Rebuild the AI-powered BDD-first test case generator from the technical spec at `testcase-gen-technical-spec.md`. Produces Gherkin test cases from BA documents + Figma screenshots, with a quality report (DeepEval) proving output quality.

**Positioning:** "The test case generator that proves its output quality."

**Scope:** Expansion — full pipeline + vision + merge + eval harness + loop verifier + web UI + CLI demo + golden dataset.

## Cross-Plan Dependencies

None. All prior plans (Phase 1 Pydantic, Loop Verifier Upgrade) are `completed`.

## Architecture

```
testcase-gen/
├── apps/
│   ├── api/                  # FastAPI (Python)
│   │   ├── models/           # Pydantic schemas (requirements, ui_inventory, merge_gap, test_case, verdict)
│   │   ├── pipeline/         # Core logic
│   │   │   ├── ingest.py     # docx/pdf/txt parsing
│   │   │   ├── extract.py    # LLM pass 1 — requirements extraction
│   │   │   ├── vision.py     # Screenshot → UI inventory
│   │   │   ├── merge.py      # Feature↔Screen mapping + gap detection
│   │   │   ├── generate.py   # LLM pass 2 — test case generation
│   │   │   ├── gemini_client.py  # Gemini API wrapper with retry
│   │   │   ├── model_router.py   # Cross-family LLM routing (Gemini/OpenRouter)
│   │   │   ├── verify.py     # Cross-family verification
│   │   │   ├── loop.py       # Gate → verify → judge → retry orchestrator
│   │   │   └── export/       # gherkin_writer.py, xlsx_writer.py
│   │   ├── evals/
│   │   │   ├── metrics.py    # DeepEval custom metrics + gate()
│   │   │   ├── calibration.py    # Labeled-bad subset calibration
│   │   │   └── datasets/     # Golden test sets + labeled_bad.json
│   │   ├── prompts/          # Versioned prompt files (extraction_v1.md, etc.)
│   │   └── server.py         # FastAPI endpoints
│   └── web/                  # Next.js
│       └── src/              # React components, pipeline UI
├── packages/shared/          # TypeScript types from Pydantic (datamodel-code-gen)
├── tests/                    # pytest suite
└── .github/workflows/        # CI: pytest + eval regression gate
```

### Pipeline Flow

```
BA Doc + Screenshots
       │
       ├──→ ingest.py ──→ extract.py (Gemini) ──→ RequirementsDocument
       │
       ├──→ vision.py (Gemini Vision) ──→ UIInventory
       │
       ├──→ merge.py ──→ MergeResult (mappings + gaps)
       │
       └──→ generate.py (Gemini) ──→ TestCaseSet
                    │
                    ├──→ gate()     (gherkin lint + dedup — FREE)
                    │
                    ├──→ verify.py  (OpenRouter Claude/GPT — cross-family)
                    │
                    └──→ loop.py    (retry with feedback, max 3 iter)
                              │
                              ├──→ gherkin_writer.py → .feature files
                              └──→ evals/metrics.py  → QualityReport
```

## Prior Implementation Recovery

From the loop-verifier plan and `.pyc` artifacts:
- **104 tests** existed across 9 test files (all models, extraction, generation, gate, loop, model_router, verify, vision/merge, eval metrics)
- **4 failed tests** in last run (test_gate + test_verify + test_gherkin)
- **Models:** `verdict.py`, `requirements.py`, `ui_inventory.py`, `merge_gap.py`, `test_case.py`
- **Pipeline:** `extract.py`, `generate.py`, `ingest.py`, `vision.py`, `merge.py`, `gemini_client.py`, `model_router.py`, `verify.py`, `loop.py`
- **Evals:** `metrics.py` (gate(), ACCoverage, GherkinValidity, CategoryBalance, Faithfulness, Duplication, InferredRatio), `calibration.py`
- **Export:** `gherkin_writer.py`
- **Web:** Static JS (api-client.js, app.js, state-manager.js, ui-renderer.js)
- Source `.py` files deleted — design recoverable, code must be rewritten

## Phases

| # | Phase | Status | Effort | Deps |
|---|-------|--------|--------|------|
| 1 | [Project Setup & Pydantic Schemas](./phase-01-project-setup-schemas.md) | completed | 4h | none |
| 2 | [Document Ingestion & Extraction Pipeline](./phase-02-extraction-pipeline.md) | completed | 5h | Phase 1 |
| 3 | [Test Case Generation & Gherkin Export](./phase-03-testcase-generation-gherkin.md) | completed | 5h | Phase 2 |
| 4 | [Vision Pipeline & Merge/Gap Detection](./phase-04-vision-merge.md) | completed | 4h | Phase 1 |
| 5 | [Quality Evaluation Harness (DeepEval)](./phase-05-eval-harness.md) | completed | 4h | Phase 3 |
| 6 | [Maker/Verifier Loop](./phase-06-loop-verifier.md) | completed | 4h | Phase 5 |
| 7 | [FastAPI Server & Pipeline API](./phase-07-server-api.md) | completed | 3h | Phase 6 |
| 8 | [Web UI, CLI Demo & Golden Dataset](./phase-08-web-ui-demo.md) | completed | 6h | Phase 7 |
| 9 | [Testing, CI/CD & Documentation](./phase-09-testing-docs.md) | completed | 5h | Phase 8 |

**Stretch items** (expansion scope, included above):
- Full vision pipeline (Phase 4)
- Loop verifier with cross-family LLM verification (Phase 6)
- Web UI with Next.js (Phase 8)
- Golden dataset curation (Phase 8)
- Calibration suite (Phase 5)

## Key Invariants (from spec)

1. `explicit` vs `inferred` distinction in extraction — foundation for hallucination metric
2. Vision model ONLY records visible elements — no behavior inference
3. Gherkin is first-class output — must pass `gherkin-official` parse gate
4. `grounding_source` mandatory for every test case
5. `Scenario Outline` + Examples table for boundary/equivalence cases — not 5 similar scenarios
6. Verifier MUST be different model family from generator (cross-family)
7. Deterministic gate runs BEFORE LLM verifier (zero-token cost)
8. Gap report shown BEFORE test cases in UI

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `gherkin-official` library stale/broken | Low | High | Fallback to `behave` parser or regex-based validation |
| Gemini API rate limits during development | Medium | Medium | Mock LLM client for testing; real calls only in integration |
| OpenRouter key missing (verify/judge) | Medium | High | Graceful degrade — skip verify, return gate-only results |
| Vision model inconsistency (Gemini Vision) | Medium | Medium | `vision_confidence` field; low-confidence screens flagged for human review |
| Source files deleted — no recovery from prior code | Certain (already happened) | Medium | Use plan docs + bytecode naming as design reference; rewrite fresh |
| Prompt versioning complexity | Low | Low | Simple file-based versioning (extraction_v1.md, v2.md) — no DB |

## Completion Criteria

- [x] Pydantic schemas match spec sections 1–4 exactly
- [x] Extract pipeline produces explicit/inferred-tagged requirements from sample BA docs
- [x] Generate pipeline produces valid Gherkin with `grounding_source` on every case
- [x] `gherkin-official` hard gate: 100% of outputs must parse
- [x] Vision pass describes only visible elements
- [x] Merge detects all 3 gap types
- [x] DeepEval metrics run and produce structured QualityReport
- [x] Loop verifier: gate → verify → retry → converge or exhaust budget
- [x] FastAPI server: POST /generate returns test cases + quality report
- [x] CLI demo processes sample doc end-to-end
- [x] Golden dataset: 1 BA doc + 20+ hand-written test cases as ground truth
- [x] All 104+ tests pass (parity with prior implementation)
- [x] Web UI renders pipeline results interactively

## Unresolved Questions

- Should the web UI be built with Next.js (spec recommendation) or extend existing static JS?
- Choice of gherkin parser: `gherkin-official` (Cucumber) vs `behave` — depends on available packages
- Golden dataset: use internal project docs or public sample? Security concern with real BA documents
