# Phase 03 — Test Case Generation & Gherkin Export

**Priority:** P1
**Status:** completed
**Effort:** 5h
**Dependencies:** Phase 2 (extraction pipeline → RequirementsDocument)

## Context Links
- Spec: `testcase-gen-technical-spec.md` sections 4 + 6 + 8.3
- Prior: `.claude/skills/testcase-gen-testcase-generation/SKILL.md`
- Prior test file: `tests/test_generation_pipeline.py` (12 tests existed)

## Overview

Build the test case generation pipeline (Pass 2 of the LLM pipeline) and Gherkin file export. Input: RequirementsDocument from Phase 2. Output: TestCaseSet with validated Gherkin + exported .feature files.

## Key Insights

- BDD-first rules from spec: Scenario Outline for boundary/equivalence, declarative steps, standardized tags, mandatory grounding_source
- Prior generation pipeline had: `generate.py` (LLM), `gherkin_writer.py` (file export), gherkin validation
- 12 generation tests existed — testing scenario/scenario_outline generation, gherkin validation, file writing, retry, export
- `gherkin-official` library or fallback to `behave` for validation
- Few-shot examples in prompt: 1 Scenario + 1 Scenario Outline with examples table

## Requirements

### Functional
- Generate test cases from RequirementsDocument via Gemini
- Enforce BDD rules: Scenario Outline for boundary/equivalence, declarative steps, @tags
- Validate Gherkin syntax (hard gate — must parse)
- Ground every case: `grounding_source` must cite original doc text
- Export to .feature files (one per feature)
- Export to .xlsx via openpyxl
- Regeneration on Gherkin validation failure

### Non-Functional
- Generation prompt versioned: `generation_v1.md`
- Few-shot examples embedded in prompt
- Gherkin validation failure → regenerate once with error context
- Declarative step check: flag steps containing "click", "type", "press"

## Architecture

```
apps/api/pipeline/
├── generate.py       # load_prompt(), build_feature_content(), run_generation()
│                     # validate_gherkin(), regenerate_on_failure()
└── export/
    ├── __init__.py
    ├── gherkin_writer.py   # write_feature_file(), format_step(), format_examples_table()
    └── xlsx_writer.py      # write_test_cases_xlsx() — basic workbook export
prompts/
└── generation_v1.md  # Few-shot prompt with 1 Scenario + 1 Scenario Outline example
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/pipeline/generate.py` | create | Generation orchestration |
| `apps/api/pipeline/export/__init__.py` | create | Export package |
| `apps/api/pipeline/export/gherkin_writer.py` | create | .feature file writer |
| `apps/api/pipeline/export/xlsx_writer.py` | create | .xlsx file writer |
| `apps/api/prompts/generation_v1.md` | create | Generation prompt + few-shot |
| `tests/fixtures/sample_requirements.json` | create | Sample RequirementsDocument fixture |
| `tests/test_generation_pipeline.py` | create | 12 generation tests |
| `tests/test_gherkin_writer.py` | create | Gherkin export tests |

## Implementation Steps

1. Write `prompts/generation_v1.md`: few-shot 1 Scenario (declarative), 1 Scenario Outline (Examples table), rules for tags/grounding/boundary
2. Implement `gherkin_writer.py`: `format_step(step)`, `format_examples_table(data)`, `write_feature_file(test_case_set, output_dir)`
3. Implement `xlsx_writer.py`: `write_test_cases_xlsx(test_case_set, output_path)` — basic sheet with TC ID, title, category, priority, steps, gherkin
4. Implement `generate.py`: `load_generation_prompt(version)`, `build_feature_content(requirements_doc)`, `run_generation(requirements_doc)`, `validate_gherkin(test_cases)` using gherkin parser, `regenerate_on_failure()`
5. Create `sample_requirements.json` fixture from sample BA doc extraction
6. Write `test_generation_pipeline.py`: test_scenario, test_scenario_outline, test_loads_prompt, test_generates_valid_output (mocked), test_rejects_missing_grounding (mocked), test_retries_on_bad_json (mocked), test_valid_gherkin, test_invalid_gherkin, test_write_file, test_build_feature_content, test_scenario_outline_valid, test_export_all_valid
7. Write `test_gherkin_writer.py`: test formats Scenario correctly, formats Scenario Outline with examples table, creates file on disk, handles empty test case set

## Todo List

- [ ] Write `prompts/generation_v1.md` with few-shot examples
- [ ] Implement `gherkin_writer.py`
- [ ] Implement `xlsx_writer.py`
- [ ] Implement `generate.py` with validation + regeneration
- [ ] Create sample requirements fixture
- [ ] Write 12 generation tests
- [ ] Write gherkin writer tests
- [ ] All tests pass

## Success Criteria
- `generate.run_generation()` returns TestCaseSet from RequirementsDocument
- Every TestCase has `grounding_source` (non-empty string)
- `Scenario Outline` used for boundary/equivalence category cases
- `validate_gherkin()` passes on valid Gherkin, raises on invalid
- `gherkin_writer.write_feature_file()` produces parseable .feature files
- Regeneration fires when gherkin validation fails
- All 12+ tests pass

## Risk Assessment
- `gherkin-official` library may be hard to install: fallback to regex-based Gherkin lint or `behave` parser
- Gemini hallucination on grounding_source: post-generation validation checks every TC has grounding
- Generation prompt quality: iterate prompt based on eval results from Phase 5

## Next Steps
- Phase 5 (eval harness) validates generation quality
- Phase 6 (loop verifier) wraps generation in retry loop
