# Phase 02 — Document Ingestion & Extraction Pipeline

**Priority:** P1
**Status:** completed
**Effort:** 5h
**Dependencies:** Phase 1 (schemas)

## Context Links
- Spec: `testcase-gen-technical-spec.md` sections 1 + 6 + 8.2
- Prior: `.claude/skills/testcase-gen-requirements-extraction/SKILL.md`
- Prior test file: `tests/test_extraction_pipeline.py` (17 tests existed)

## Overview

Build the document ingestion layer (docx/pdf/txt parsing) and the LLM-powered requirements extraction pipeline. This is Pass 1 of the pipeline — BA documents in, structured RequirementsDocument out with explicit/inferred tagging.

## Key Insights

- Prior extraction pipeline had: `ingest.py` (parse), `extract.py` (LLM), `gemini_client.py` (API wrapper with retry)
- 17 extraction tests existed — testing parse, prompt loading, title extraction, markdown stripping, JSON parsing, retry logic, end-to-end
- Prompt versioning is file-based: `prompts/extraction_v1.md`, `extraction_v2.md` etc.
- `source_location` field mandatory on every feature — enables traceability

## Requirements

### Functional
- Parse .txt (direct), .docx (python-docx), .pdf (PyPDF2)
- Detect source_type from extension
- Strip markdown code fences from LLM JSON responses
- Extract title from first heading or first non-empty line
- Fill user prompt template with document text
- Call Gemini API via `gemini_client.py` with retry (max 3 attempts)
- Parse JSON response into RequirementsDocument model
- Tag every acceptance criteria as `explicit` or `inferred`
- Return ExtractionConfidence with counts

### Non-Functional
- Gemini API key from env var `GEMINI_API_KEY`
- Prompt files in `apps/api/prompts/` directory
- LLM call timeout: 60s
- JSON parse failures → retry with error context, up to 3 attempts
- Max token budget for extraction: 8192 output tokens

## Architecture

```
apps/api/pipeline/
├── ingest.py          # parse_txt(), parse_docx(), parse_pdf(), parse_document() dispatcher
├── extract.py         # load_prompt(), fill_template(), run_extraction(), strip_markdown_fences()
├── gemini_client.py   # get_client(), generate_content() with retry, GeminiClient wrapper
prompts/
└── extraction_v1.md   # Prompt template with {document_text} placeholder
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/pipeline/__init__.py` | create | Pipeline package |
| `apps/api/pipeline/ingest.py` | create | Document parsing |
| `apps/api/pipeline/extract.py` | create | LLM extraction orchestration |
| `apps/api/pipeline/gemini_client.py` | create | Gemini API wrapper |
| `apps/api/prompts/extraction_v1.md` | create | Extraction prompt template |
| `tests/fixtures/sample_ba_doc.txt` | create | Sample BA document for testing |
| `tests/fixtures/sample_ba_doc.docx` | create | Sample docx for testing |
| `tests/test_extraction_pipeline.py` | create | 17+ extraction tests |

## Implementation Steps

1. Implement `ingest.py`: file extension dispatch, txt (read text), docx (python-docx paragraphs), pdf (PyPDF2 pages), raise on unsupported extension
2. Implement `prompts/extraction_v1.md`: role = senior BA analyst, output JSON only, explicit/inferred rules, mandatory source_location, handling messy docs
3. Implement `gemini_client.py`: GeminiClient class, `generate_content()` with retry on rate limit, configurable model/temperature
4. Implement `extract.py`: `load_prompt(version)`, `fill_template(prompt, doc_text)`, `strip_markdown_fences(raw_json)`, `extract_title(text)`, `run_extraction(file_path)`
5. Create sample BA document in `tests/fixtures/` (3-5 features, mix of explicit/inferred criteria)
6. Write `test_extraction_pipeline.py`: test_source_type_mapping, test_file_not_found, test_unsupported_extension, test_parses_txt, test_strips_fences, test_no_fences, test_extracts_heading, test_extracts_first_line_no_heading, test_empty_text, test_load_prompt, test_prompt_file_not_found, test_fills_template, test_parses_valid_json (mocked LLM), test_retries_on_json_error, test_raises_after_max_failures, test_end_to_end
7. Add `tests/conftest.py` with pytest fixtures (mock Gemini client, sample documents)

## Todo List

- [ ] Implement `ingest.py` with txt/docx/pdf support
- [ ] Write `prompts/extraction_v1.md` prompt template
- [ ] Implement `gemini_client.py` with retry wrapper
- [ ] Implement `extract.py` orchestration
- [ ] Create sample BA documents in fixtures
- [ ] Write 17 extraction tests
- [ ] All tests pass

## Success Criteria
- `ingest.parse_document("sample.txt")` returns raw text
- `ingest.parse_document("sample.docx")` returns raw text
- `ingest.parse_document("sample.pdf")` returns raw text
- Unknown extension raises ValueError
- `extract.strip_markdown_fences()` handles ```json blocks
- `extract.run_extraction()` returns RequirementsDocument with explicit/inferred counts
- `extract.run_extraction()` retries on JSON parse failure, max 3 times
- ExtractionConfidence fields sum correctly
- All 17 tests pass

## Risk Assessment
- Gemini API unavailable during tests: mock via pytest fixture, integration test only in CI
- PDF parsing quality varies: PyPDF2 may miss tables/images — acceptable for v1
- Prompt versioning conflicts: always load latest version, store version in extraction result

## Next Steps
- Phase 3 (test case generation) consumes RequirementsDocument output
- Phase 4 (vision) runs independently on screenshots
