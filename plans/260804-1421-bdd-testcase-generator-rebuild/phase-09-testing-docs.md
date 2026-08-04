# Phase 09 — Testing, CI/CD & Documentation

**Priority:** P2
**Status:** completed
**Effort:** 5h
**Dependencies:** Phase 8 (web UI, CLI, golden dataset)

## Context Links
- Spec: `testcase-gen-technical-spec.md` section 7 (CI workflow)
- Prior: 104 tests across 9 test files
- Prior: `.github/workflows/` planned but not implemented on disk

## Overview

Comprehensive test suite across all modules, CI/CD pipeline with eval regression gate, and project documentation. Achieve parity with prior implementation (104+ tests, all passing) and extend coverage.

## Key Insights

- Prior test inventory from pytest cache (104 tests):
  - test_models.py: 24 tests
  - test_extraction_pipeline.py: 17 tests
  - test_generation_pipeline.py: 12 tests
  - test_gherkin_writer.py: (new)
  - test_vision_merge.py: 10 tests
  - test_eval_metrics.py: 14 tests
  - test_gate.py: 7 tests
  - test_model_router.py: 8 tests
  - test_verify.py: 6 tests
  - test_loop.py: 8 tests
  - test_server.py: (new, ~10 tests)
- Prior 4 test failures (Jun 28 snapshot): test_invalid_gherkin, test_gate_fails_on_bad_gherkin, test_gate_combined_failures, test_prompt_excludes_generator_reasoning
- CI: pytest + eval regression gate on prompt version changes

## Requirements

### Testing
- Unit tests for all model files (24 tests)
- Unit tests for extraction pipeline (17 tests)
- Unit tests for generation pipeline (12 tests)
- Unit tests for gherkin writer (6 tests)
- Unit tests for vision + merge (10 tests)
- Unit tests for eval metrics (14 tests)
- Unit tests for gate (7 tests)
- Unit tests for model router (8 tests)
- Unit tests for verify (6 tests)
- Unit tests for loop (8 tests)
- Integration tests for server (10 tests)
- Integration tests for CLI (5 tests)
- Eval regression tests: run golden dataset through pipeline, verify quality scores

### CI/CD
- GitHub Actions workflow: install deps → run pytest → check coverage → eval regression gate
- Eval regression gate: if golden dataset scores drop > 5%, fail CI
- Prompt version tracking: on prompt change, trigger regression eval

### Documentation
- `README.md` with project overview, setup, usage
- `CLAUDE.md` with project instructions
- `docs/project-overview-pdr.md` — product overview
- `docs/system-architecture.md` — architecture diagram + data flow
- `docs/code-standards.md` — coding conventions
- `.env.example` — all required env vars with descriptions

## Architecture

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures, mock LLM clients
├── fixtures/                      # Test data
│   ├── sample_ba_doc.txt
│   ├── sample_ba_doc.docx
│   ├── sample_requirements.json
│   ├── sample_test_cases.json
│   └── sample_screenshot.png
├── test_models.py                 # 24 tests
├── test_extraction_pipeline.py    # 17 tests
├── test_generation_pipeline.py    # 12 tests
├── test_gherkin_writer.py         # 6 tests
├── test_vision_merge.py           # 10 tests
├── test_eval_metrics.py           # 14 tests
├── test_gate.py                   # 7 tests
├── test_model_router.py           # 8 tests
├── test_verify.py                 # 6 tests
├── test_loop.py                   # 8 tests
├── test_server.py                 # 10 tests
├── test_cli.py                    # 5 tests
└── test_eval_regression.py        # 3 tests

.github/workflows/
└── ci.yml                         # CI pipeline

docs/
├── project-overview-pdr.md
├── system-architecture.md
└── code-standards.md
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `tests/conftest.py` | create | Shared fixtures |
| `tests/test_gherkin_writer.py` | create | Gherkin writer tests |
| `tests/test_server.py` | create | Server integration tests |
| `tests/test_cli.py` | create | CLI tests |
| `tests/test_eval_regression.py` | create | Eval regression gate |
| `.github/workflows/ci.yml` | create | CI pipeline |
| `README.md` | create | Project README |
| `CLAUDE.md` | create | Project Claude instructions |
| `.env.example` | create | Environment variables template |
| `docs/project-overview-pdr.md` | create | Product overview |
| `docs/system-architecture.md` | create | Architecture docs |
| `docs/code-standards.md` | create | Code standards |

## Implementation Steps

### Testing
1. Create `tests/conftest.py` with:
   - `mock_gemini_client` fixture — mock Gemini API
   - `mock_openrouter_client` fixture — mock OpenRouter API
   - `sample_requirements_doc` fixture — load from fixtures/
   - `sample_test_case_set` fixture — valid TestCaseSet
2. Implement all test files as specified in prior phases
3. Write `test_server.py`: test_health, test_extract_endpoint, test_generate_endpoint, test_status_polling, test_gherkin_export, test_xlsx_export, test_invalid_file_upload, test_missing_api_key, test_merge_endpoint, test_vision_endpoint
4. Write `test_cli.py`: test_help, test_missing_file, test_runs_with_txt, test_output_files_exist, test_verbose_flag
5. Write `test_eval_regression.py`: test_golden_dataset_scores, test_prompt_version_change_regression, test_scores_within_threshold

### CI/CD
6. Write `.github/workflows/ci.yml`:
   ```yaml
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
         - run: pip install -r requirements.txt
         - run: pytest tests/ --cov=apps/api --cov-report=term
         - run: pytest tests/test_eval_regression.py
     eval-regression-gate:
       needs: test
       if: github.event_name == 'pull_request'
       runs-on: ubuntu-latest
       steps:
         - run: python -c "import json; ..." # compare golden scores
   ```

### Documentation
7. Write `README.md`: project overview, quick start, architecture diagram link, API docs link
8. Write `CLAUDE.md`: role, workflows, hook protocol, modularization rules, docs structure
9. Write `.env.example`: GEMINI_API_KEY, OPENROUTER_API_KEY with descriptions
10. Write `docs/project-overview-pdr.md`: product description, positioning, user journey
11. Write `docs/system-architecture.md`: Mermaid diagram + component descriptions
12. Write `docs/code-standards.md`: naming conventions, file size limits, code quality rules

## Todo List

- [ ] Create `conftest.py` with shared fixtures
- [ ] Implement all test files (127+ tests)
- [ ] Ensure 0 test failures
- [ ] Write server integration tests
- [ ] Write CLI tests
- [ ] Write eval regression tests
- [ ] Create CI workflow
- [ ] Write `README.md`
- [ ] Write `CLAUDE.md`
- [ ] Write `.env.example`
- [ ] Write `docs/` documentation files
- [ ] Verify eval regression gate works

## Success Criteria
- All 127+ tests pass (0 failures)
- Test coverage > 80% on `apps/api/`
- CI pipeline passes: pytest + coverage + eval regression
- Eval regression gate fails if golden dataset scores drop > 5%
- All documentation files present and accurate
- `.env.example` lists all required env vars

## Risk Assessment
- Test flakiness from LLM calls: all LLM-dependent tests use mocks
- Coverage tooling: use pytest-cov, enforce > 80% but don't block on marginal misses
- CI runner lacks API keys: eval regression tests skip on missing keys (mark with pytest.skip)
- Golden dataset quality: review by hand before committing

## Next Steps
- Project complete — ready for `/ck:cook` to implement all phases
