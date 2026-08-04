# Phase 06 — Maker/Verifier Loop

**Priority:** P2
**Status:** completed
**Effort:** 4h
**Dependencies:** Phase 5 (eval harness — gate() function)

## Context Links
- Prior: `plans/260628-2226-loop-verifier-upgrade/` (all 8 phases complete)
- Prior deliverables: verdict.py, gate(), model_router.py, verify.py, loop.py, calibration
- Prior tests: test_gate.py (7 tests), test_model_router.py (8 tests), test_verify.py (6 tests), test_loop.py (8 tests)

## Overview

Implement maker/verifier loop: generate → gate → verify → judge → retry. Verifier uses different model family (cross-family: Gemini generates, Claude/GPT verifies via OpenRouter) to avoid correlated errors. Budgeted retry with max 3 iterations.

## Key Insights

- Prior implementation had this fully working (99/99 tests passed per plan)
- 5 key invariants from prior plan documented in `plan.md` line 29-35
- `model_router.py` is single source of truth for role-based LLM routing
- `verify.py` excludes generator reasoning from verifier input
- Loop budget: max_iter=3, max_usd=$0.50
- Gate runs first (free, deterministic) — no LLM cost unless gate passes
- Judge escalates to different model (GPT) for low-confidence verification

## Architecture

```
                           +------------------+
                           |   Requirements   |
                           +--------+---------+
                                    |
                    +---------------v---------------+
                    |          loop.run()            |
                    |  budget: max_iter=3, max=$0.50 |
                    +---------------+---------------+
                                    |
                    +---------------v---------------+
                    |   generate(feedback=prev)     |  <-- Gemini
                    +---------------+---------------+
                                    |
                    +---------------v---------------+
                    |     gate() - deterministic    |  <-- FREE
                    +-------+-------+---------------+
                        fail|   pass|
                            |       |
                    [retry w/ |  +---v--------------+
                     feedback]|  | verify() via     |  <-- OpenRouter Claude/GPT
                              |  | cross-family LLM |
                              |  +---+--------------+
                              |      |
                              |  pass|            fail
                              |      |              |
                              |  [DONE]    +--------v--------+
                              |            | low confidence? |
                              |            +--------+--------+
                              |                     | yes
                              |            +--------v--------+
                              |            | judge() via     |  <-- OpenRouter GPT
                              |            | GPT/Qwen        |
                              |            +--------+--------+
                              |                     |
                              +<--- feedback loop --+
```

## Requirements

### Functional
- `model_router.py`: ROLES dict (generate → Gemini, verify → Claude via OpenRouter, judge → GPT via OpenRouter)
- `verify.py`: takes output + source + rubric, NOT generator reasoning
- `loop.py`: orchestrate generate → gate → verify → judge cycle
- Budget tracking: max 3 iterations, max $0.50 USD, no_progress_stop
- Graceful degrade: if no OpenRouter key, skip verify, return gate-only result
- Return LoopResult with actual_iterations, total_cost, final_output

### Non-Functional
- OpenRouter API key from env var `OPENROUTER_API_KEY`
- Verify timeout: 30s per call
- Judge escalation only on confidence < 0.7
- VerificationError handling with retry (not fallback)
- Budget tracking uses simplified per-iteration cost model ($0.03/iter)

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/pipeline/model_router.py` | create | Role-based LLM client routing |
| `apps/api/pipeline/verify.py` | create | Cross-family verification |
| `apps/api/pipeline/loop.py` | create | Loop orchestrator |
| `apps/api/prompts/verify.md` | create | Verifier prompt template |
| `tests/test_gate.py` | create | Gate function tests (7) |
| `tests/test_model_router.py` | create | Model router tests (8) |
| `tests/test_verify.py` | create | Verify pipeline tests (6) |
| `tests/test_loop.py` | create | Loop orchestrator tests (8) |

## Implementation Steps

1. Implement `model_router.py`: `get_client(role: str)` returning Gemini/OpenRouter client, `ROLES = {"generate": {...}, "verify": {...}, "judge": {...}}`
2. Write `prompts/verify.md`: takes output + source + rubric, returns VerifierVerdict with pass/fail + failed_criteria
3. Implement `verify.py`: `verify(test_cases, source, rubric)`, `_verify_with_client()`, VerifyError handling
4. Implement `loop.py`: `run(requirements, max_iter=3, max_usd=0.50)`, `_call_verifier()`, `_call_judge()`, no_progress detection
5. Write tests:
   - `test_gate.py`: test_gate_passes_on_valid, test_gate_passes_on_empty, test_gate_fails_on_bad_gherkin, test_gate_fails_on_duplicates, test_gate_captures_both_failure_types, test_gate_captures_gherkin_failure, test_gate_combined_failures
   - `test_model_router.py`: test_generate_and_verify_different_models, test_verify_returns_openrouter_client, test_judge_role_different_from_verify, test_unknown_role_raises, test_get_fallback_for_unknown_role_raises, test_get_fallback_models_for_judge
   - `test_verify.py`: test_load_verify_prompt, test_prompt_excludes_generator_reasoning, test_prompt_template_contains_only_output_and_source, test_verify_pass_on_clean_output, test_verify_fail_on_problematic_output, test_verify_overwrites_model_field
   - `test_loop.py`: test_loop_passes_on_first_attempt, test_loop_retries_on_gate_failure, test_loop_respects_max_iterations, test_loop_stops_on_two_identical_gate_failures, test_no_progress_detector, test_no_progress_different_failures, test_low_confidence_below_threshold, test_high_confidence_not_low

## Todo List

- [ ] Implement `model_router.py` with role-based routing
- [ ] Write `prompts/verify.md` verifier prompt
- [ ] Implement `verify.py` with cross-family verification
- [ ] Implement `loop.py` orchestrator with budget tracking
- [ ] Write 7 gate tests
- [ ] Write 8 model router tests
- [ ] Write 6 verify tests
- [ ] Write 8 loop tests
- [ ] All 29 tests pass

## Success Criteria
- `model_router.get_client("generate")` returns Gemini client
- `model_router.get_client("verify")` returns OpenRouter client
- `verify()` never receives generator reasoning in its input
- `gate()` returns GateResult with gherkin_pass and dup_count
- `loop.run()` runs up to max_iter iterations or until pass
- `loop.run()` stops on 2 identical gate failures (no_progress)
- Graceful degrade when OPENROUTER_API_KEY missing
- Budget tracking: actual_iterations reported correctly
- All 29 tests pass

## Risk Assessment
- OpenRouter API unavailable: graceful degrade (skip verify, gate-only)
- Verify schema drift: retry with schema-fix prompt, fallback to gate-only
- Budget tracking precision: use simplified model (fixed per-iter cost), not real-time pricing
- Infinite loop: no_progress_stop=True, 2 identical failures triggers break

## Next Steps
- Phase 7 (server) wires loop into FastAPI endpoints
