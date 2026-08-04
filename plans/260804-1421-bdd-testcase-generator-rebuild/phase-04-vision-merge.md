# Phase 04 — Vision Pipeline & Merge/Gap Detection

**Priority:** P2 (expensive + complex, can be deferred)
**Status:** completed
**Effort:** 4h
**Dependencies:** Phase 1 (schemas — ui_inventory.py, merge_gap.py)

## Context Links
- Spec: `testcase-gen-technical-spec.md` sections 2 + 3 + 6 (vision prompt) + 8.5
- Prior test file: `tests/test_vision_merge.py` (10 tests existed)

## Overview

Build the vision analysis pipeline (screenshot → UI inventory) and the merge/gap detection engine. Vision model ONLY records visible elements — no behavior inference. Merge compares requirements against UI inventory to find 3 gap types.

## Key Insights

- Vision model must describe what is visible, not guess behavior — this is the anti-hallucination gate
- `vision_confidence` field flags screens where model is unsure (low/medium/high)
- 10 vision/merge tests existed: test_feature_screen_match, test_perfect_match_no_gaps, test_requirement_without_design_gap, test_design_without_requirement_gap, test_validation_mismatch, test_empty_inventory, test_empty_requirements, test_mime_type_detection, test_no_api_key
- Gap report shown BEFORE test cases in UI — immediate user value
- This phase is the most expensive (API cost) and hardest to debug — build AFTER text pipeline is stable

## Requirements

### Functional
- Accept image files (PNG, JPG) as screenshots
- Call Gemini Vision API with screenshot + vision prompt
- Parse response into UIInventory model
- Detect MIME type from file extension/binary header
- Graceful handling when no API key configured
- Merge RequirementsDocument + UIInventory:
  - Map features to screens by name/text similarity
  - Detect requirement_without_design gaps
  - Detect design_without_requirement gaps
  - Detect validation_mismatch gaps (field constraints differ)

### Non-Functional
- Vision prompt versioned: `vision_v1.md`
- Max 5 screenshots per call (batch limit)
- Vision model: Gemini 2.5 Pro Vision or Gemini 2.0 Flash
- Merge uses text similarity (basic token overlap) for feature↔screen mapping

## Architecture

```
apps/api/pipeline/
├── vision.py          # analyze_screenshot(), mime_type_from_file(), run_vision_pipeline()
├── merge.py           # map_features_to_screens(), detect_gaps(), merge_and_analyze()
prompts/
├── vision_v1.md       # "Describe only what is visible" prompt
└── merge_v1.md        # Gap detection prompt (compares 2 JSONs)
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/pipeline/vision.py` | create | Vision API integration |
| `apps/api/pipeline/merge.py` | create | Merge & gap detection |
| `apps/api/prompts/vision_v1.md` | create | Vision analysis prompt |
| `apps/api/prompts/merge_v1.md` | create | Gap detection prompt |
| `tests/fixtures/sample_screenshot.png` | create | Placeholder screenshot |
| `tests/test_vision_merge.py` | create | 10 vision + merge tests |

## Implementation Steps

1. Write `prompts/vision_v1.md`: role = UI auditor, "describe only what is visible", no behavior inference, output per Section 2 schema
2. Write `prompts/merge_v1.md`: compare 2 JSON documents, detect 3 gap types, output per Section 3 schema
3. Implement `vision.py`: `mime_type_from_file(path)`, `run_vision_pipeline(screenshot_paths)` → UIInventory, handle no-API-key gracefully
4. Implement `merge.py`: `map_features_to_screens(requirements, ui_inventory)` via text similarity, `detect_gaps(mappings, requirements, ui_inventory)`, `merge_and_analyze(requirements, ui_inventory)` → MergeResult
5. Create placeholder test screenshot
6. Write `test_vision_merge.py`: test_feature_screen_match, test_perfect_match_no_gaps, test_requirement_without_design_gap, test_design_without_requirement_gap, test_validation_mismatch, test_empty_inventory, test_empty_requirements, test_mime_type_detection, test_no_api_key, test_merge_result_structure

## Todo List

- [ ] Write `prompts/vision_v1.md`
- [ ] Write `prompts/merge_v1.md`
- [ ] Implement `vision.py` with Gemini Vision calls
- [ ] Implement `merge.py` with gap detection logic
- [ ] Create test screenshot fixture
- [ ] Write 10 vision/merge tests
- [ ] All tests pass

## Success Criteria
- `vision.run_vision_pipeline()` returns UIInventory with screen elements
- Elements have `visible_constraints` and `visible_states` (only what was seen)
- `vision_confidence` present on each screen
- `merge.map_features_to_screens()` produces FeatureScreenMapping list
- `merge.detect_gaps()` finds all 3 gap types correctly
- Validation mismatch detected when field constraints differ between docs and UI
- All 10 tests pass

## Risk Assessment
- Gemini Vision API cost: batch screenshots, use Flash model for initial pass, Pro for confirm
- Vision accuracy varies: low confidence screens → flag for human review, don't block pipeline
- Screenshot naming convention: recommend `<screen_id>_<screen_name>.png` pattern
- Merge text similarity is basic (token overlap) — sufficient for v1 but may miss semantic matches

## Next Steps
- Phase 8 (web UI) displays gap report before test cases
- MergeResult feeds into generation pipeline (Phase 3) for richer test case context
