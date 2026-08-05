# Phase 02 — Proxy-Mutation Score

**Priority:** P2
**Status:** complete
**Effort:** 3h
**Dependencies:** Phase 1 (needs SBERT model for embedding similarity checks)

## Overview

Add a proxy for mutation score since BDD/Gherkin tests lack executable code.
For each test case, ask the LLM: "If the implementation had these specific bugs, would this test catch them?"
Score as ratio of bugs caught vs total bugs.

## Architecture

```
TestCase
    ↓
LLM prompt: "List 3 bugs this test COULD catch, and 2 bugs it would MISS"
    ↓
compute_proxy_mutation(test_cases, client=None) → float
    ↓
evaluate_all() includes proxy_mutation at 10% weight
```

## Implementation Steps

### Step 1: Build proxy-mutation prompt

```
You are a mutation testing expert. Given the Gherkin test case below,
list 3 specific implementation bugs this test WOULD catch, and
2 bugs it would MISS (despite the test passing).

Test case:
{gherkin_text}

Respond with JSON:
{
  "bugs_caught": ["bug1", "bug2", "bug3"],
  "bugs_missed": ["bug1", "bug2"]
}
```

### Step 2: Implement compute_proxy_mutation()
```python
def compute_proxy_mutation(
    test_cases: TestCaseSet,
    client: GeminiClient | None = None
) -> float:
    client = client or get_client()
    if not client.available:
        return 1.0  # skip when no API key

    scores = []
    for tc in test_cases.test_cases:
        try:
            raw = client.generate_content(PROXY_MUTATION_PROMPT.format(
                gherkin_text=gherkin_writer.format_scenario(tc)
            ))
            result = json.loads(strip_markdown_fences(raw))
            caught = len(result["bugs_caught"])
            missed = len(result["bugs_missed"])
            score = caught / (caught + missed) if (caught + missed) > 0 else 0.5
            scores.append(score)
        except Exception:
            scores.append(0.5)  # neutral on failure
    return sum(scores) / len(scores) if scores else 1.0
```

### Step 3: Integrate into evaluate_all()
- Add compute_proxy_mutation() call in evaluate_all()
- Weight: 10% of overall score
- Warning: < 0.60 (tests catch fewer than 60% of possible bugs)

### Step 4: Graceful degrade
- Skip proxy-mutation when no API key available (score = 1.0, no penalty)
- Fall back to neutral 0.5 on LLM errors
- Max 5 TCs evaluated (random sample) to control cost

## Related Code Files

| File | Action | Description |
|------|--------|-------------|
| `apps/api/evals/metrics.py` | modify | Add compute_proxy_mutation() |
| `apps/api/prompts/proxy_mutation_v1.md` | create | LLM prompt for mutation proxy |

## Todo List
- [ ] Create proxy_mutation_v1.md prompt
- [ ] Implement compute_proxy_mutation() with graceful degrade
- [ ] Sample max 5 TCs for cost control
- [ ] Integrate into evaluate_all() at 10% weight
- [ ] Add warning threshold

## Success Criteria
- Proxy-mutation returns float 0.0–1.0
- No API key → returns 1.0 (no penalty)
- Max 5 TC sample to control cost (or configurable limit)
- LLM errors → neutral 0.5 fallback
