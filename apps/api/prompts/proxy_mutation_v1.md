You are a mutation testing expert. Given the Gherkin test case below,
list 3 specific implementation bugs this test WOULD catch, and
2 bugs it would MISS (despite the test passing).

Test case:
{gherkin_text}

Respond with JSON only (no prose, no markdown fences):
{
  "bugs_caught": ["bug1", "bug2", "bug3"],
  "bugs_missed": ["bug1", "bug2"]
}
