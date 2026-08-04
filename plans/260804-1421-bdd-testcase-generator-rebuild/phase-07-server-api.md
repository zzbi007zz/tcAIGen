# Phase 07 — FastAPI Server & Pipeline API

**Priority:** P2
**Status:** completed
**Effort:** 3h
**Dependencies:** Phase 6 (loop verifier)

## Context Links
- Spec: `testcase-gen-technical-spec.md` section 7 (repo skeleton)
- Prior: `apps/api/server.py` (from loop-verifier plan — POST /generate with budget param)

## Overview

Wire the complete pipeline into a FastAPI server. Expose endpoints for the full multi-step pipeline, file upload, and quality report retrieval.

## Key Insights

- Prior server had `POST /generate` with budget parameter
- This is a long-running pipeline — async endpoints with background task support
- Multi-step pipeline: ingest → extract → (vision) → merge → generate → gate → verify → loop
- Client needs progress updates — use polling (GET /status/{job_id}) not streaming for v1

## Requirements

### Functional
- `POST /extract` — upload BA doc → RequirementsDocument
- `POST /vision` — upload screenshots → UIInventory
- `POST /merge` — RequirementsDocument + UIInventory → MergeResult
- `POST /generate` — full pipeline → TestCaseSet + QualityReport
- `GET /status/{job_id}` — poll generation progress
- `GET /export/{job_id}/gherkin` — download .feature files
- `GET /export/{job_id}/xlsx` — download spreadsheet
- `GET /prompts` — list available prompt versions
- Pipeline state persisted in memory (dict backend) for v1

### Non-Functional
- File upload: multipart/form-data, max 10MB per doc, 5MB per screenshot
- Async pipeline via BackgroundTasks
- CORS middleware for web frontend
- Health check endpoint: `GET /health`
- Error responses: structured JSON with error code and detail

## Architecture

```
apps/api/server.py
├── FastAPI app setup + CORS
├── POST /extract          # upload doc → run_extraction() → RequirementsDocument
├── POST /vision           # upload images → run_vision_pipeline() → UIInventory
├── POST /merge            # {requirements, ui_inventory} → merge_and_analyze() → MergeResult
├── POST /generate         # upload doc [+ screenshots] → loop.run() → TestCaseSet + QualityReport
├── GET  /status/{job_id}  # poll progress
├── GET  /export/{job_id}/gherkin  # zip of .feature files
├── GET  /export/{job_id}/xlsx     # xlsx download
├── GET  /prompts           # list prompt versions
└── GET  /health            # {"status": "ok"}

In-memory pipeline state:
{
  job_id: {
    "status": "processing"|"complete"|"error",
    "progress": 0.0-1.0,
    "result": TestCaseSet | None,
    "quality_report": QualityReport | None,
    "error": str | None
  }
}
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/server.py` | create | FastAPI application |
| `tests/test_server.py` | create | API integration tests |

## Implementation Steps

1. Initialize FastAPI app with CORS (allow localhost:3000 for Next.js)
2. Implement in-memory job store with job_id generation (uuid4)
3. Implement `POST /extract` — validate file extension, call extract.run_extraction(), return RequirementsDocument
4. Implement `POST /vision` — validate image files, call vision.run_vision_pipeline(), return UIInventory
5. Implement `POST /merge` — accept JSON body, call merge.merge_and_analyze(), return MergeResult
6. Implement `POST /generate` — background task calling loop.run(), return job_id immediately
7. Implement `GET /status/{job_id}` — return job state from store
8. Implement `GET /export/{job_id}/gherkin` — generate .feature files in temp dir, return zip
9. Implement `GET /export/{job_id}/xlsx` — generate xlsx, return file
10. Implement `GET /prompts` — list files in prompts/ directory
11. Implement `GET /health` — simple ok response
12. Write `test_server.py` with integration tests for each endpoint

## Todo List

- [ ] Create FastAPI app with CORS
- [ ] Implement job store
- [ ] Implement `POST /extract`
- [ ] Implement `POST /vision`
- [ ] Implement `POST /merge`
- [ ] Implement `POST /generate` with background task
- [ ] Implement `GET /status/{job_id}`
- [ ] Implement export endpoints
- [ ] Implement health check and prompts listing
- [ ] Write server integration tests
- [ ] All tests pass

## Success Criteria
- `POST /extract` returns RequirementsDocument from uploaded .txt/.docx/.pdf
- `POST /generate` returns job_id, pipeline runs in background
- `GET /status/{job_id}` returns progress and final result
- `GET /export/{job_id}/gherkin` returns valid .feature zip
- Health check responds 200
- CORS allows web frontend requests
- Error responses are structured JSON

## Risk Assessment
- Pipeline takes 30-120s: polling is acceptable for v1, upgrade to WebSocket later
- Memory store lost on restart: acceptable for v1, Redis in v2
- Large doc uploads (>10MB): enforce size limit in FastAPI

## Next Steps
- Phase 8 (web UI) consumes these API endpoints
- Phase 9 (testing) adds integration tests
