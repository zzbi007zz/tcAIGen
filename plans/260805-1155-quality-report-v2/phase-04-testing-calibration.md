# Phase 04 — Testing & Calibration

**Priority:** P2
**Status:** complete
**Effort:** 3h
**Dependencies:** Phase 1, 2, 3

## Overview

Comprehensive testing of all new metrics and recalibration of golden dataset thresholds. Ensure no regression on existing quality scores while new metrics provide meaningful differentiation between good and bad outputs.

## Implementation Steps

### Step 1: Unit tests for new metrics (test_eval_metrics.py)
Add tests for:
- `test_semantic_consistency_on_sample` — verify > 0.80 for known-good match
- `test_semantic_consistency_mismatch` — verify < 0.60 for unrelated pair
- `test_semantic_faithfulness_blended` — verify blended score
- `test_semantic_dedup_catches_paraphrase` — verify > 0.95 similarity detected
- `test_proxy_mutation_skips_without_client` — returns 1.0 when no API key
- `test_proxy_mutation_graceful_degrade` — returns 0.5 on LLM error

### Step 2: Golden dataset calibration
- Run full pipeline on golden dataset (sample_ba_doc.md → 21 ground truth TCs)
- Compare quality report scores: old (6 metrics) vs new (9 metrics)
- Verify score stays >= 70 (no regression)
- Check that semantic consistency on golden dataset >= 0.80
- Check that SBERT-enhanced faithfulness is >= existing lexical faithfulness

### Step 3: Labeled bad case calibration
- Run new metrics on labeled_bad.json (7 hand-labeled bad cases)
- Verify new metrics correctly identify bad cases (semantic consistency < 0.60, proxy-mutation < 0.60)
- Ensure overall score for bad cases is lower than golden dataset

### Step 4: Threshold tuning
- Analyze SBERT cosine distributions on golden dataset to pick thresholds
- Tune semantic consistency: warning at 0.80, critical at 0.60
- Tune semantic dedup: flag at 0.95
- Tune proxy-mutation: warning at 0.60

### Step 5: Eval regression test update
- Update test_eval_regression.py to include new metrics
- Ensure CI regression gate works with new score weights

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `tests/test_eval_metrics.py` | modify | Add 6+ new test functions |
| `tests/test_eval_regression.py` | modify | Update for new metrics |
| `apps/api/evals/metrics.py` | modify | Threshold tuning |

## Todo List
- [ ] Add 6+ unit tests for new metrics
- [ ] Run golden dataset calibration
- [ ] Run labeled_bad case calibration
- [ ] Tune thresholds based on distributions
- [ ] Update eval regression test
- [ ] Verify all 132+ tests pass
- [ ] Verify CI regression score >= 70

## Success Criteria
- All existing 132 tests still pass
- New metrics have proper unit test coverage
- Golden dataset score >= 70 with new weights
- Labeled bad cases score lower than golden dataset
- Thresholds tuned against actual data distributions
