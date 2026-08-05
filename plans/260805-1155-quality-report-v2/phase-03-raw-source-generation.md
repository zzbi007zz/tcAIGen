# Phase 03 — Raw Source in Generation Prompt

**Priority:** P1 (low effort, high impact)
**Status:** complete
**Effort:** 1h
**Dependencies:** none

## Overview

Research shows including raw source context alongside structured data improves LLM generation quality by up to **+19.67% branch coverage** (docstring/context inclusion effect). For BDD test cases, this means giving the LLM both the structured `requirements_json` AND the raw source document text for richer lexical anchors and better faithfulness.

## Implementation Steps

### Step 1: Update generation prompt
Add `{source_document}` placeholder to `generation_v1.md`:
```markdown
# CONTEXT
Below is the original BA document text and its structured requirements extraction.
Use the original text for lexical grounding. Use the structured JSON for feature structure.

ORIGINAL DOCUMENT:
{source_document}

STRUCTURED REQUIREMENTS:
{requirements_json}
```

### Step 2: Update generate.py to pass source text
```python
def run_generation(
    requirements_doc: RequirementsDocument,
    client: Optional[GeminiClient] = None,
    prompt_version: str = "v1",
    source_text: str = "",  # NEW param
) -> TestCaseSet:
    prompt = load_generation_prompt(prompt_version).replace(
        "{requirements_json}", build_feature_content(requirements_doc)
    ).replace(
        "{source_document}", source_text  # NEW
    )
    ...
```

### Step 3: Update loop.py and server.py to pass source text
- `Loop._generator()` signature already supports kwargs via `run_generation(requirements)`
- Update server.py `_run_job()`: pass `source=ingest.parse_document(doc_path)` as source_text
- Update cli.py similarly

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/prompts/generation_v1.md` | modify | Add ORIGINAL DOCUMENT section + {source_document} |
| `apps/api/pipeline/generate.py` | modify | Accept source_text param, inject into prompt |
| `apps/api/pipeline/loop.py` | modify | Pass source_text to generator |
| `apps/api/server.py` | modify | Pass source to loop.run() |
| `apps/cli.py` | modify | Pass source to generate pipeline |

## Todo List
- [ ] Add {source_document} to generation prompt
- [ ] Update run_generation() to accept source_text
- [ ] Update loop.py to pass source_text
- [ ] Update server.py _run_job() to pass source
- [ ] Update cli.py to pass source

## Success Criteria
- Generation prompt includes both structured JSON and raw source text
- No regression: golden dataset score stays >= 70
- Original source text included (not truncated, within token limits)
