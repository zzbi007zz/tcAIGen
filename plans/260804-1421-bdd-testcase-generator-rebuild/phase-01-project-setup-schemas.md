# Phase 01 — Project Setup & Pydantic Schemas

**Priority:** P1 (blocks all other phases)
**Status:** completed
**Effort:** 4h

## Context Links
- Spec: `testcase-gen-technical-spec.md` sections 1–4 + 7
- Prior: `plans/260610-0754-phase1-pydantic-schemas/phase-01-pydantic-schemas.md`
- Prior pipeline models from loop-verifier plan

## Overview

Create the project skeleton and data model layer. Pydantic schemas mirror spec sections 1–4 exactly. Every other module depends on these models.

## Key Insights

- Prior implementation had 5 model files: `requirements.py`, `ui_inventory.py`, `merge_gap.py`, `test_case.py`, `verdict.py`
- 24 model tests existed (all passing in last run)
- Schemas must distinguish `explicit` vs `inferred` (grounding for hallucination metric)
- `verdict.py` models (FailedCriterion, VerifierVerdict, GateResult, LoopBudget) from prior loop verifier — reusable design

## Requirements

### Functional
- 4 Pydantic model modules matching spec JSON schemas exactly
- `document_meta` with source_type: word|pdf|paste
- `ExplicitOrInferred` union type for all acceptance criteria
- `vision_confidence` field on screens (high|medium|low)
- Gap types enum: requirement_without_design | design_without_requirement | validation_mismatch
- Gherkin block with scenario_type, tags, examples_table
- `grounding_source` mandatory field

### Non-Functional
- Models must be serializable/deserializable round-trip
- `model_dump_json()` and `model_validate_json()` work without data loss
- `from __future__ import annotations` for forward references
- Models in `__init__.py` exports for clean imports

## Architecture

```
apps/api/models/
├── __init__.py            # Re-exports all models
├── requirements.py        # DocumentMeta, AcceptanceCriterion, InputValidation, Feature, RequirementsDocument, ExtractionConfidence
├── ui_inventory.py        # UIElement, Screen, UIInventory
├── merge_gap.py           # FeatureScreenMapping, Gap, MergeResult
├── test_case.py           # TestStep, Gherkin, TestCase, TestCaseSet
└── verdict.py             # FailedCriterion, VerifierVerdict, GateResult, LoopBudget
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/models/requirements.py` | create | Section 1 schema |
| `apps/api/models/ui_inventory.py` | create | Section 2 schema |
| `apps/api/models/merge_gap.py` | create | Section 3 schema |
| `apps/api/models/test_case.py` | create | Section 4 schema |
| `apps/api/models/verdict.py` | create | Verdict/loop models |
| `apps/api/models/__init__.py` | create | Re-exports |
| `apps/__init__.py` | create | Package init |
| `apps/api/__init__.py` | create | Package init |
| `requirements.txt` | create | FastAPI, pydantic, google-genai, openai, deepeval, etc. |
| `tests/test_models.py` | create | Round-trip + validation tests |

## Implementation Steps

1. Create directory structure per spec section 7
2. Create `requirements.txt` with: fastapi, uvicorn, pydantic>=2, google-genai, openai, deepeval, python-docx, PyPDF2, gherkin-official, openpyxl
3. Set up virtualenv and install deps
4. Implement `requirements.py` — 6 classes: DocumentMeta, AcceptanceCriterion, InputValidation, Feature, RequirementsDocument, ExtractionConfidence
5. Implement `ui_inventory.py` — 3 classes: UIElement, Screen, UIInventory
6. Implement `merge_gap.py` — 3 classes: FeatureScreenMapping, Gap (with GapType enum), MergeResult
7. Implement `test_case.py` — 4 classes: TestStep, Gherkin, TestCase, TestCaseSet
8. Implement `verdict.py` — 4 classes: FailedCriterion, VerifierVerdict, GateResult, LoopBudget
9. Wire `__init__.py` with all exports
10. Write `test_models.py` with round-trip tests for all 20+ model classes
11. Verify all models import cleanly and serialize/deserialize

## Todo List

- [ ] Create project skeleton per spec section 7
- [ ] Write `requirements.txt` and install deps
- [ ] Implement `requirements.py` (Section 1 schema)
- [ ] Implement `ui_inventory.py` (Section 2 schema)
- [ ] Implement `merge_gap.py` (Section 3 schema)
- [ ] Implement `test_case.py` (Section 4 schema)
- [ ] Implement `verdict.py` (loop verifier models)
- [ ] Wire `__init__.py` exports
- [ ] Write `test_models.py` with 24+ tests
- [ ] Run tests — all must pass

## Success Criteria
- All 5 model files importable via `from apps.api.models import *`
- JSON round-trip works for every model: serialize → deserialize → re-serialize === original
- `explicit_criteria_count + inferred_criteria_count` validated on ExtractionConfidence
- GapType enum prevents invalid gap types
- `grounding_source` field non-nullable on TestCase
- 24+ model tests pass

## Risk Assessment
- Schema drift from spec: validate against spec JSON examples literally
- Pydantic v2 breaking changes: pin pydantic>=2.0, use `model_validate` not `parse_obj`

## Next Steps
- Phase 2 (extraction pipeline) depends on requirements.py models
- Phase 4 (vision) depends on ui_inventory.py models
- Phase 3 (generation) depends on test_case.py models
