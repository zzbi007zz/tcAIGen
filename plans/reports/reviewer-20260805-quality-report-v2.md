# Code Review: Quality Report v2

## Code Review Summary

### Scope
- Files: apps/api/evals/{semantic.py,proxy_mutation.py,gate.py,metrics.py}, apps/api/pipeline/{generate.py,loop.py}, apps/cli.py, apps/api/prompts/{generation_v1.md,proxy_mutation_v1.md}, tests/*, requirements.txt
- Focus: recent Quality Report v2 changes
- Scout findings: dependents of evaluate_all (apps/cli.py, apps/api/server.py), loop generator fallback, pytest-env gating of new metrics

### Overall Assessment
Solid, well-scoped implementation. Graceful-degradation design is consistent. Score math verified (weights sum to 1.0). Two correctness concerns (TypeError masking, proxy prompt ignore), one test-validity concern (regression gate free-passes the new metrics), plus minor issues.

### Critical Issues
None — no security/data-loss/breaking issues found. `evaluate_all` new `client` param is optional, backwards-compatible.

### High Priority
1. **TypeError fallback masks real generator errors** — `apps/api/pipeline/loop.py:60-64`. `except TypeError` around `self._generator(requirements, source_text=source)` catches TypeErrors raised *inside* the default `run_generation` (e.g. malformed LLM JSON iteration), silently retrying without source context and losing the injected `{source_document}`. Narrow the check: use `inspect.signature(self._generator)` or `functools` to decide arity up-front instead of try/except.
2. **Regression tests free-pass the metrics they gate** — `apps/api/evals/metrics.py:148-151,219-224` + `tests/test_eval_regression.py`. Under pytest (no SBERT_TESTS/PROXY_TESTS), `consistency=None`→substituted as 1.0 and `mutation=1.0`. So "golden 98.1 ≥ 70" and "bad 56.9–71.9" are computed with 25% of the score auto-granted. The acceptance numbers validate the formula shape, not SBERT/proxy discrimination. Recommend: CI job with SBERT_TESTS=1 asserting semantic_consistency actually separates good/bad fixtures, and a recorded-fixture proxy test (PROXY_TESTS with stub client) to pin the mutation path.

### Medium Priority
3. **`max_samples` parameter silently ignored for small sets** — `apps/api/evals/proxy_mutation.py:52-54`. `random.sample` only when `len(cases) > max_samples`; with ≤5 TCs the *seeded determinism* claim holds, but callers passing `max_samples=1` on a 3-TC set get all 3 scored. Tests pass `max_samples=1` with a 1-response mock — a 2-TC fixture would consume the mock list and raise. Either truncate (`cases[:max_samples]`) or document.
4. **Exception-swallowing erases error context** — `semantic.py` (3x bare `except Exception: return None/[]`) and `proxy_mutation.py:60-61`. Documented intent, but a persistent failure (e.g. bad model cache, malformed LLM JSON for all 5 samples) silently degrades to "no penalty" (score 1.0 / None) with no signal. At minimum `logging.warning(...)` in each handler so production degradation is observable.
5. **cli.py parses the source document twice** — `apps/cli.py:47,57` (`parse_document` in run_generation and again in evaluate_all). PDF/DOCX parsing is non-trivial; parse once, reuse. Same duplication exists in `apps/api/server.py:115,123`.
6. **Semantic faithfulness penalizes empty grounding inconsistently** — `apps/api/evals/semantic.py:89-91`. Empty `grounding_source` strings are still embedded and scored against chunks (low cosine) only when *some* other TC has grounding (`any()` check) — mixed sets get dragged down differently than all-empty sets (None→fall back to lexical). Either drop empty groundings from the SBERT pass or score them 0.0 explicitly to match lexical behavior.

### Low Priority
7. **Proxy prompt undermines scored variability** — `apps/api/prompts/proxy_mutation_v1.md` instructs exactly "3 caught / 2 missed", making the model's own counts structurally biased to 0.6 regardless of test quality. The metric discriminates only via refusal/deviation. Consider asking the model to enumerate honestly without fixed counts.
8. **`_strip_inferred_tag` regex only strips trailing tag** — `apps/api/evals/semantic.py:41`; `compute_inferred_ratio` matches "inferred" anywhere in the string (`metrics.py:131`), so groundings like "AC1 (inferred, low confidence)" keep the tag in the SequenceMatcher match. Minor ratio noise.
9. **O(n²) dedup with model encode each call** — `semantic.detect_semantic_duplicates` re-encodes all TCs on every `evaluate_all`; fine at current scale, note if batch jobs grow.

### Edge Cases Found by Scout
- `evaluate_all(test_cases)` with `requirements=None` and no pytest env: SBERT consistency skipped (guarded) but `detect_semantic_duplicates` still runs → model download attempted on any caller path. OK but worth noting for server latency.
- `source_doc` containing only whitespace/newlines → `compute_semantic_faithfulness` returns None via empty-chunks check → lexical path returns 1.0 when `source_doc` is falsy but 0.0-weighted overlap when whitespace-only (`source_tokens` non-None but empty → every grounding scores 0). Inconsistent: `source_doc=" \n"` ≠ `source_doc=""`.
- Proxy: LLM returns `{"bugs_caught": "string"}` → `len("string")`=6 — type-confused counts. Low risk but `isinstance(list)` guard would harden.

### Positive Observations
- Lazy SBERT singleton with clean degrade contract (None/[]) is well designed.
- Score weights sum to exactly 1.00; dup penalty preserved from v1.
- `__all__` re-export keeps `gate`/`detect_duplicates` backwards-compatible after extraction to gate.py.
- Seeded sampling makes proxy-mutation deterministic for fixed input.
- Prompt template versioning (`proxy_mutation_v1.md`) matches existing convention.

### Recommended Actions
1. Replace TypeError sniffing in loop.py with signature inspection (High).
2. Add CI regression leg with SBERT_TESTS=1 + stubbed proxy client so the 98.1/56.9 numbers exercise the real metrics (High).
3. Truncate to max_samples or fix docstring; add logging in degrade handlers; parse source doc once in cli/server (Medium).
4. Loosen fixed 3/2 counts in proxy prompt; add isinstance guards on LLM JSON (Low).

### Unresolved Questions
- Is score inflation via None→1.0 substitution (consistency/mutation unavailable) acceptable as product behavior, or should the report surface "metrics unavailable" explicitly to users?
