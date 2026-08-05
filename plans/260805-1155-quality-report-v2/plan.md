---
title: "Quality Report v2 — SBERT Consistency, Mutation Proxy, Full Framework"
description: "Upgrade the 6-metric quality report to 9 metrics: add SBERT semantic consistency, semantic faithfulness, semantic dedup, proxy-mutation score, and include raw source in generation. Aligns with 2025–2026 research consensus on multi-dimensional LLM test quality evaluation."
status: complete
priority: P2
effort: 10h
branch: main
tags: [quality, metrics, sbert, mutation, faithfulness, semantic]
created: 2026-08-05
---

# Quality Report v2 — SBERT Consistency + Mutation Proxy

## Overview

Research across IEEE, ACM, ICLR 2025–2026 converges: no single metric can validate LLM-generated test case quality. Our current 6-metric report covers 6/8 recommended dimensions. This plan adds the 2 missing dimensions (semantic consistency, proxy-effectiveness) and upgrades 2 existing ones (faithfulness, dedup).

**Current:** 6 metrics (AC Coverage, Category Balance, Faithfulness-lexical, Inferred Ratio, Gherkin Validity, Text-based Dedup)
**Target:** 9 metrics (add Semantic Consistency, SBERT Faithfulness, Semantic Dedup, Proxy-Mutation)

## Architecture

```
new metrics.py structure:
├── compute_ac_coverage()        [unchanged]
├── compute_category_balance()   [unchanged]
├── compute_faithfulness()       [upgraded: blend lexical + SBERT]
├── compute_inferred_ratio()     [unchanged]
├── compute_gherkin_validity()   [unchanged]
├── compute_semantic_consistency() [NEW]  SBERT test↔req similarity
├── compute_proxy_mutation()     [NEW]  LLM "would this catch a bug?"
├── compute_semantic_dedup()     [NEW]  SBERT dedup >0.95 threshold
├── evaluate_all()               [upgraded: new weights, new metrics]
```

## Phases

| # | Phase | Status | Effort | Deps |
|---|-------|--------|--------|------|
| 1 | SBERT Semantic Consistency + Enhanced Faithfulness + Dedup | complete | 3h | none |
| 2 | Proxy-Mutation Score | complete | 3h | Phase 1 |
| 3 | Raw Source in Generation Prompt | complete | 1h | none |
| 4 | Testing & Calibration | complete | 3h | Phase 1, 2, 3 |

## Key Dependencies
- `sentence-transformers` pip package (80MB model download, runs locally, zero API cost)
- Existing golden dataset for calibration

## Updated Score Weights

```
Overall Score =
  0.20 * AC Coverage
+ 0.15 * Category Balance (negative >= 20%)
+ 0.15 * Faithfulness (50% lexical + 50% SBERT)
+ 0.15 * Semantic Consistency (SBERT, target >= 0.80)
+ 0.15 * Gherkin Validity
+ 0.10 * Inferred Ratio (informational)
+ 0.10 * Proxy-Mutation (LLM judged)
- 2 pts per duplicate (text OR semantic)
```

## Completion Criteria
- [ ] SBERT computes semantic consistency per test-case↔acceptance-criterion pair
- [ ] Faithfulness blends 50% lexical token overlap + 50% SBERT semantic similarity
- [ ] Semantic dedup catches >0.95 similarity pairs
- [ ] Proxy-mutation LLM prompt asks "if this behavior broke, would this test catch it?"
- [ ] Raw source doc included in generation prompt alongside structured requirements
- [ ] All existing 132 tests still pass
- [ ] New metrics tested in test_eval_metrics.py
- [ ] Golden dataset calibration shows improved differentiation (good vs bad cases)
- [ ] No regression: golden dataset score stays >= 70

## Unresolved Questions
- SBERT model: `all-MiniLM-L6-v2` (80MB, fast) vs `all-mpnet-base-v2` (420MB, better)?
- Multilingual SBERT for Vietnamese docs?
- Proxy-mutation: run per-test-case or batch?
- Semantic consistency threshold: 0.80 or 0.75?
