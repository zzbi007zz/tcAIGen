# Phase 01 — SBERT Semantic Consistency + Enhanced Faithfulness + Semantic Dedup

**Priority:** P1
**Status:** complete
**Effort:** 3h
**Dependencies:** none

## Overview
Add 3 new evaluation capabilities using Sentence-BERT (local, zero API cost):
1. Semantic Consistency — per-test-case similarity to referenced acceptance criterion
2. Enhanced Faithfulness — blend 50% lexical + 50% SBERT semantic
3. Semantic Dedup — catch paraphrased duplicates text-based dedup misses

## Architecture

```
SentenceTransformer("all-MiniLM-L6-v2")
    ↓ lazy init (singleton, loaded once)
    ↓
compute_semantic_consistency()     → per-TC embedding vs referenced AC
compute_semantic_faithfulness()    → grounding_source embedding vs source doc
compute_semantic_dedup()           → pairwise TC titles, threshold >0.95
```

## Implementation Steps

### Step 1: Install dependency
```bash
.venv/bin/pip install sentence-transformers
echo "sentence-transformers>=3.0" >> requirements.txt
```

### Step 2: Add lazy-loaded SBERT model to metrics.py
```python
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None

def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def _cosine_sim(a, b) -> float:
    return float((a @ b) / (a.norm() * b.norm()))
```

### Step 3: Add compute_semantic_consistency()
- For each test case, find the acceptance criterion cited in grounding_source
- Encode pair (test_case.gherkin.title, ac_text)
- Compute cosine similarity
- Score: average across all test cases
- Warning thresholds: < 0.80 = warning, < 0.60 = critical

### Step 4: Upgrade compute_faithfulness()
- Keep existing lexical (token overlap) score
- Add SBERT semantic: encode grounding_source + source_doc
- Blend: `0.5 * lexical_score + 0.5 * semantic_score`
- Same warning threshold: < 0.80

### Step 5: Upgrade dedup in evaluate_all()
- Current: text-based, >0.92 threshold
- Add: SBERT pairwise cosine similarity on test case titles
- Flag as duplicate if text-based OR SBERT >= 0.95
- Combined dedup penalty in overall score

### Step 6: Update evaluate_all() weights
```
Overall Score =
  0.20 * AC Coverage
+ 0.15 * Category Balance
+ 0.15 * Faithfulness (blended)
+ 0.15 * Semantic Consistency
+ 0.15 * Gherkin Validity
+ 0.10 * Inferred Ratio
+ 0.10 * Proxy-Mutation (placeholder, Phase 2)
- 2 pts per duplicate (text OR semantic)
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/evals/metrics.py` | modify | Add SBERT model, 3 new functions, updated weights |
| `requirements.txt` | modify | Add sentence-transformers |

## Todo List
- [ ] Install sentence-transformers
- [ ] Add lazy-loaded SBERT singleton
- [ ] Implement compute_semantic_consistency()
- [ ] Upgrade compute_faithfulness() to blend lexical + semantic
- [ ] Upgrade dedup to include semantic dedup
- [ ] Update evaluate_all() score weights
- [ ] Add new metric warnings

## Success Criteria
- SBERT model loads once (lazy init), reused across metrics
- Semantic consistency computes for all TCs with findable AC references
- Faithfulness outputs blended score (lexical + SBERT)
- Semantic dedup identifies pairs where title cosine > 0.95
- No regression in existing golden dataset scores
- All 132 tests still pass
