# Phase 08 — Web UI, CLI Demo & Golden Dataset

**Priority:** P3
**Status:** completed
**Effort:** 6h
**Dependencies:** Phase 7 (FastAPI server)

## Context Links
- Spec: `testcase-gen-technical-spec.md` sections 5 (report UI) + 7 (repo skeleton) + 8.6 (CLI demo) + golden dataset
- Prior web code: `apps/web/` static JS (api-client.js, app.js, state-manager.js, ui-renderer.js)
- Prior: `apps/web/css/style.css`

## Overview

Build a web UI (Next.js) for the interactive pipeline, a CLI demo tool for end-to-end processing, and curate the golden dataset (1 BA doc + 20+ hand-written test cases as ground truth).

## Key Insights

- Gap report should display BEFORE test cases in UI — immediate value for users
- Quality Report UI is the screenshot for the landing page
- CLI demo is for progress proof video — no UI needed, just terminal
- Golden dataset is foundational — without it, "proves its output quality" is empty
- Prior web layer was static JS — this rebuild upgrades to Next.js for richer interactivity

## Requirements

### Web UI
- **Upload page**: drag-and-drop BA doc + screenshots
- **Pipeline progress**: step-by-step status (Extracting → Merging → Generating → Verifying)
- **Gap report panel**: shown before test cases
- **Test case browser**: sortable/filterable table of generated TCs
- **Quality Report dashboard**: overall score + metric breakdown + drill-down to cases
- **Export buttons**: download .feature zip, download .xlsx
- **Prompt version selector** for generation

### CLI Demo
- Single command: `python -m apps.cli run <ba_doc_path> [--screenshots <dir>]`
- Outputs: .feature files + Quality Report markdown + timing summary
- Works without web UI or server
- Prints progress to stdout

### Golden Dataset
- 1 BA document sample (e.g., login/registration flow — common test scenario)
- 20+ hand-crafted test cases as ground truth
- Coverage spanning positive, negative, edge, boundary categories
- Correct Gherkin for each case
- Stored in `apps/api/evals/datasets/golden/`

## Architecture

```
apps/
├── cli.py                # CLI entry point: argparse → pipeline.run()
└── web/                  # Next.js app
    ├── package.json
    ├── next.config.js
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx
    │   │   ├── page.tsx           # Main pipeline page
    │   │   └── globals.css
    │   ├── components/
    │   │   ├── FileUpload.tsx     # Drag-and-drop upload
    │   │   ├── PipelineProgress.tsx  # Step-by-step status
    │   │   ├── GapReport.tsx      # Gap detection display
    │   │   ├── TestCaseBrowser.tsx # Sortable/filterable TC table
    │   │   ├── QualityDashboard.tsx # Metric cards + breakdown
    │   │   └── ExportPanel.tsx    # Download buttons
    │   └── lib/
    │       └── api-client.ts      # FastAPI client
apps/api/evals/datasets/
└── golden/
    ├── sample_ba_doc.md           # Sample BA document
    └── ground_truth_tcs.json      # 20+ hand-written test cases
```

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/cli.py` | create | CLI demo entry point |
| `apps/web/package.json` | create | Next.js project config |
| `apps/web/next.config.js` | create | Next.js config |
| `apps/web/src/app/layout.tsx` | create | Root layout |
| `apps/web/src/app/page.tsx` | create | Main pipeline page |
| `apps/web/src/app/globals.css` | create | Global styles |
| `apps/web/src/components/FileUpload.tsx` | create | Upload component |
| `apps/web/src/components/PipelineProgress.tsx` | create | Progress indicator |
| `apps/web/src/components/GapReport.tsx` | create | Gap display |
| `apps/web/src/components/TestCaseBrowser.tsx` | create | TC table |
| `apps/web/src/components/QualityDashboard.tsx` | create | Quality report dashboard |
| `apps/web/src/components/ExportPanel.tsx` | create | Export buttons |
| `apps/web/src/lib/api-client.ts` | create | API client |
| `apps/api/evals/datasets/golden/sample_ba_doc.md` | create | Sample BA doc |
| `apps/api/evals/datasets/golden/ground_truth_tcs.json` | create | 20+ golden TCs |

## Implementation Steps

### CLI Demo
1. Create `apps/cli.py`: argparse with required doc path, optional screenshots dir, verbose flag
2. Wire pipeline steps: ingest → extract → (vision) → merge → generate → gate → verify → loop
3. Output: .feature files to `./output/`, quality report to stdout, timing to `./output/report.md`
4. Print progress: `[1/5] Extracting requirements...` style

### Golden Dataset
5. Write sample BA doc: login/registration flow with 3-4 features, 10+ acceptance criteria
6. Hand-write 20+ test cases: 8 positive, 6 negative, 3 edge, 3 boundary
7. Ensure correct Gherkin syntax for all cases
8. Verify ground truth against schema

### Web UI
9. Init Next.js project in `apps/web/` with TypeScript
10. Implement `api-client.ts` with fetch wrappers for all server endpoints
11. Build `FileUpload.tsx` with drag-and-drop, progress indicator
12. Build `PipelineProgress.tsx` showing current step with animated UI
13. Build `GapReport.tsx` — list of gaps with type badge and note
14. Build `TestCaseBrowser.tsx` — sortable table with category/priority filters
15. Build `QualityDashboard.tsx` — score cards + metric bars + warning links
16. Build `ExportPanel.tsx` — download buttons for .feature and .xlsx
17. Wire main `page.tsx` — upload → progress → gaps → TCs → quality → export
18. Add loading, error, and empty states for all components

## Todo List

- [ ] Implement `apps/cli.py`
- [ ] Write sample BA doc for golden dataset
- [ ] Hand-write 20+ golden test cases
- [ ] Init Next.js project
- [ ] Implement API client (`api-client.ts`)
- [ ] Build FileUpload component
- [ ] Build PipelineProgress component
- [ ] Build GapReport component
- [ ] Build TestCaseBrowser component
- [ ] Build QualityDashboard component
- [ ] Build ExportPanel component
- [ ] Wire main page with full flow
- [ ] Add loading/error/empty states

## Success Criteria
- CLI processes sample BA doc end-to-end and produces .feature files
- CLI demo works without server or web UI
- Golden dataset: 20+ hand-written TCs with correct Gherkin
- Web UI uploads doc → shows pipeline progress → displays gaps → shows TCs → shows quality report
- Gap report panel renders BEFORE test cases
- Quality dashboard shows all 6 metrics with scores
- Export buttons produce valid .feature zip and .xlsx
- Loading states, error states, empty states handled for all components

## Risk Assessment
- Next.js setup overhead: use `create-next-app` + Tailwind for rapid prototyping
- CLI vs server code duplication: CLI uses same pipeline module, only adds argparse + stdout output
- Golden dataset quality: review by hand, verify Gherkin parses, spot-check against metrics

## Next Steps
- Phase 9 (testing, CI/CD, docs) validates the full system
