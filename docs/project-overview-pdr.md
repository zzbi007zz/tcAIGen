# Project Overview (PDR)

**Product:** BDD-First Test Case Generator
**Positioning:** the test case generator that proves its output quality.

## Problem
QA teams write test cases manually from BA documents. LLM generators exist but
produce unverifiable output (hallucinated requirements, broken Gherkin, duplicates).

## Solution
Pipeline that generates Gherkin test cases from BA docs + UI screenshots and
attaches a quality report proving coverage, validity, and grounding.

## User Journey
1. Upload BA doc (+ optional Figma screenshots)
2. See gap report first (requirement/design mismatches) — immediate value
3. Browse generated test cases (filter/sort by category, priority)
4. Review quality report (6 metrics, warnings linked to specific TCs)
5. Export `.feature` zip or `.xlsx`

## Key Invariants
1. `explicit` vs `inferred` tagging in extraction (hallucination metric foundation)
2. Vision records only visible elements — no behavior inference
3. Gherkin is first-class output — 100% must parse (hard gate)
4. `grounding_source` mandatory per test case
5. Scenario Outline + Examples for boundary/equivalence cases
6. Verifier is a different model family than the generator
7. Deterministic gate runs before the LLM verifier (zero-token)
8. Gap report shown before test cases in UI

## Success Metrics
- Golden dataset quality score >= 70/100 (regression-gated in CI)
- Gherkin validity 100% on all shipped outputs
- AC coverage >= 95% target on golden dataset
