# Phase 05 — Quality Evaluation Harness (DeepEval)

**Priority:** P2
**Status:** completed
**Effort:** 4h
**Dependencies:** Phase 3 (test case generation → TestCaseSet)

## Context Links
- Spec: `testcase-gen-technical-spec.md` section 5
- Prior test file: `tests/test_eval_metrics.py` (14 tests existed)
- Prior: `apps/api/evals/calibration.py` + `apps/api/evals/datasets/labeled_bad.json`

## Overview

Build the Quality Report engine using DeepEval custom metrics. Runs automatically after every generation. Shows 1 summary score + breakdown with links from each warning to the specific test case.

## Key Insights

- Prior eval had 14 tests (all passing) and gate() function in `metrics.py`
- Metrics: AC Coverage, Category Balance, Faithfulness (G-Eval), Inferred Ratio, Gherkin Validity (hard gate), Duplication
- Gherkin Validity is a **hard gate** — 100% must parse or trigger regeneration
- Inferred Ratio is informational (flags missing docs, not tool quality)
- Duplication uses embedding similarity, flags > 0.92 for auto-merge suggestion
- Calibration: Cohen's kappa on labeled_bad subset (7 entries existed prior)

## Requirements

### Functional

| Metric | Implementation | Threshold |
|--------|---------------|-----------|
| AC Coverage | % criteria with >=1 TCs / total testable | >=95% pass, <85% warn |
| Category Balance | positive : negative : edge ratio | flag if negative < 30% |
| Faithfulness | DeepEval G-Eval on grounding_source | score >= 0.8 |
| Inferred Ratio | % cases grounding=inferred | informational only |
| Gherkin Validity | gherkin parser on all TCs | 100% hard gate |
| Duplication | Embedding similarity pairwise | flag > 0.92 |

### Non-Functional
- `evaluate_all()` returns structured QualityReport with overall_score, breakdown, warnings
- Each warning links to specific tc_id
- gate() function for deterministic checks (zero-token, used by Phase 6)
- Calibration: Cohen's kappa against labeled ground truth

## Architecture

```
apps/api/evals/
├── __init__.py
├── metrics.py          # ACCoverage, CategoryBalance, Faithfulness, InferredRatio,
│                       # GherkinValidity, Duplication, evaluate_all(), gate()
├── calibration.py      # load_labeled_set(), compute_kappa(), run_calibration()
└── datasets/
    └── labeled_bad.json    # Known-bad test cases with human labels
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/evals/__init__.py` | create | Eval package |
| `apps/api/evals/metrics.py` | create | 6 metrics + gate() + evaluate_all() |
| `apps/api/evals/calibration.py` | create | Kappa calibration |
| `apps/api/evals/datasets/labeled_bad.json` | create | 7 labeled bad entries |
| `tests/fixtures/sample_test_cases.json` | create | Test case set for eval testing |
| `tests/test_eval_metrics.py` | create | 14 eval metric tests |

## Implementation Steps

1. Implement `metrics.py`:
   - `compute_ac_coverage(test_cases, requirements)` → score + warnings
   - `compute_category_balance(test_cases)` → ratio + flag
   - `compute_faithfulness(test_cases, source_doc)` → G-Eval score 0–1
   - `compute_inferred_ratio(test_cases)` → percentage + insight text
   - `validate_gherkin_syntax(test_cases)` → pass/fail + parse errors
   - `detect_duplicates(test_cases)` → similar pairs > 0.92
   - `evaluate_all(test_cases, requirements, source_doc)` → QualityReport
   - `gate(test_cases)` → GateResult (gherkin_pass, dup_count, passed bool)
2. Implement `calibration.py`: load labeled set, compute Cohen's kappa, run against metrics
3. Create `labeled_bad.json` with 7 hand-labeled entries (known failures)
4. Create `sample_test_cases.json` fixture
5. Write `test_eval_metrics.py`: test_full_coverage, test_partial_coverage, test_good_balance, test_low_negative_ratio, test_all_grounded, test_empty_grounding_source, test_all_gherkin_valid, test_invalid_gherkin, test_invalid_gherkin_reported, test_no_duplicates, test_similar_cases, test_mixed_grounding, test_full_report, test_gate_passes_on_valid

## Todo List

- [ ] Implement `metrics.py` with 6 evaluation functions
- [ ] Implement `gate()` function for deterministic checks
- [ ] Implement `calibration.py` with Cohen's kappa
- [ ] Create `labeled_bad.json` calibration dataset
- [ ] Create sample test cases fixture
- [ ] Write 14 eval metric tests
- [ ] Write calibration tests
- [ ] All tests pass

## Success Criteria
- `evaluate_all()` returns QualityReport with overall_score 0–100
- AC Coverage correctly counts covered vs total criteria
- Category Balance flags when negative < 30%
- Gherkin Validity hard-fails on unparseable Gherkin
- Duplication flags pairs > 0.92 similarity
- `gate()` returns correct GateResult for valid/invalid inputs
- Calibration yields interpretable kappa score
- All 14+ tests pass

## Risk Assessment
- DeepEval G-Eval requires OpenAI API key: mock in tests, real in CI
- Embedding similarity needs sentence-transformers or API: use basic cosine on TF-IDF for v1, upgrade later
- Gherkin parser library compatibility: test with both gherkin-official and behave fallback

## Next Steps
- Phase 6 (loop verifier) wraps generation + gate + verify
- Phase 8 (web UI) displays quality report
