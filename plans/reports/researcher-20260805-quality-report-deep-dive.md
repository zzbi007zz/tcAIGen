# Research Report: Quality Report Deep Dive — Ensuring Generated Test Case Quality

**Date:** 2026-08-05
**Sources:** 4 research queries across IEEE, ACM, arXiv, industry frameworks

## Executive Summary

The 2025–2026 consensus: no single metric can validate LLM-generated test case quality. Effective evaluation requires a multi-dimensional framework combining **validity** (hallucination rate, semantic entropy), **effectiveness** (mutation score, HackRate), **readability** (smell density), and **grounding** (faithfulness/groundedness). Our current 6-metric quality report covers ~60% of the recommended dimensions — strong on grounding and static validation, missing on runtime effectiveness (mutation score) and semantic consistency (reverse-generation checks). The highest-leverage upgrade: add a **semantic entropy / SBERT-based consistency check** between generated test cases and original requirements.

## Research Methodology
- Sources consulted: 25+ papers and frameworks
- Date range: 2025–2026 (active research area)
- Key terms: LLM test case quality, mutation score, faithfulness metrics, RAGAS, DeepEval, SBERT semantic validation, reverse generation, G-Eval, Hallucination Rate

---

## Key Findings

### 1. The Multi-Dimensional Consensus

| Dimension | What It Measures | Industry Standard | Our Coverage |
|-----------|-----------------|-------------------|-------------|
| **Validity** | Does the test pass/parse? | Build rate, Semantic Entropy | Gherkin Validity (parse gate) |
| **Effectiveness** | Does it catch bugs? | Mutation Score, HackRate | MISSING |
| **Grounding** | Is it faithful to source? | Faithfulness, Groundedness | Faithfulness (token overlap) |
| **Coverage** | Are all requirements covered? | AC/Feature Coverage | AC Coverage |
| **Balance** | Are scenario types diverse? | Category Ratios | Category Balance |
| **Uniqueness** | Are tests not duplicative? | Dedup Rate, Smell Density | Duplication check |
| **Semantic Consistency** | Do tests semantically match reqs? | SBERT Similarity, Reverse Gen | MISSING |
| **Traceability** | Can each test trace to a req? | Requirement-Test Matrix | grounding_source (partial) |

**Verdict:** 6/8 dimensions covered. Two critical gaps: runtime effectiveness and semantic consistency.

### 2. What's Missing: Mutation Score

Multiple 2025 papers (MUTGEN, PRIMG, ICTSS 2025) converge on the same finding: **100% code coverage can coexist with 4% mutation score.** Mutation testing — injecting faults into code and checking if tests catch them — is the gold standard for effectiveness. However, it requires executable code, which our BDD/Gherkin tests don't have at generation time.

**Alternative for BDD test cases:** "Speculation testing" — for each generated test case, ask an LLM: "If this behavior were broken, would this test catch it?" Score as ratio of breakable behaviors covered. This approximates mutation testing without executable code.

**Or:** Use the **reverse generation + SBERT consistency check** (Farchi et al., 2025) as a proxy — if tests semantically reconstruct the original requirements, they're likely effective.

### 3. What's Missing: Semantic Consistency (High-Impact, High-Feasibility)

Farchi et al. (Nov 2025) demonstrated a closed-loop methodology:
1. Generate test cases from requirements (→ what we do)
2. **Reverse-generate** requirements from the test cases
3. Score semantic similarity via **SBERT cosine similarity:**
   - \>0.8 = strong match / near-duplicate
   - 0.6–0.8 = related but distinct (needs review)
   - 0.3–0.6 = weak alignment (missing details)
   - <0.3 = no meaningful relation (probable hallucination)
4. Iteratively refine until thresholds met

**This is directly implementable** for our quality report. SBERT is lightweight, runs locally, and requires no API calls. It would give us a 7th metric — "semantic consistency" — that directly answers "do these test cases actually test what the requirements say?"

### 4. Grounding/Faithfulness: Our Approach vs. State of Art

| Approach | How It Works | Strengths | Weaknesses |
|----------|------------|-----------|-----------|
| **Our token overlap** | Intersection / \|grounding\| | Fast, deterministic, zero-API-cost | Fails on paraphrases, penalizes extra context |
| **RAGAS Faithfulness** | LLM decomposes answer into claims, checks each against context | Catches semantic fabrications | Requires LLM call, costs tokens |
| **DeepEval Faithfulness** | G-Eval chain-of-thought judge | Debuggable reasons, pytest-native | Requires LLM call, costs tokens |
| **SBERT Semantic Similarity** | Embedding vectors + cosine similarity | Fast, local, no API cost | Threshold tuning needed per domain |

**Recommendation:** Keep token overlap as the fast deterministic gate. Add SBERT similarity as a complementary metric (see Implementation below).

### 5. Prompt Engineering: Highest-Leverage Quality Control

Across all 2025 papers, prompt engineering consistently outweighs model choice for test case quality:

| Technique | Quality Gain | Cost Increase |
|-----------|-------------|---------------|
| CoT + Self-Consistency | Significantly improves ENC, NFC, Clarity | Moderate |
| Docstring/Context inclusion | +19.67% branch coverage | Low |
| Mutation-guided feedback (MUTGEN) | Superior to EvoSuite/simple prompting | High |
| Reasoning models (O1) | 3–5% marginal gain over GPT-4o | 3× higher cost |

**Our prompt already includes:** Role definition, explicit constraints, self-quality gate, negative ratio targets, verbatim grounding requirement. This aligns with best practices.

**Missing:** We don't include the original source document text in the generation prompt (only structured JSON). Including raw source text alongside structured requirements could improve faithfulness by giving the LLM additional lexical anchors.

### 6. Deduplication: Beyond Simple Threshold

Our current dedup uses >92% text similarity. Research shows:
- LLMs often generate redundant tests for the same behavior (different wording, same test)
- **TC-Bench (ICLR 2026)** uses "WrongSelect" to aggressively filter redundant error codes, showing that unfiltered benchmarks inflate HackRate from ~50% to ~100%
- SBERT-based deduplication (cosine similarity >0.95) catches semantic duplicates that text-based methods miss

**Recommendation:** Add SBERT-based semantic dedup alongside our current text-based dedup.

---

## Implementation Recommendations

### Priority 1: SBERT Semantic Consistency Metric (est. 3h)

Add a 7th metric to `metrics.py`:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # 80MB, runs locally

def compute_semantic_consistency(
    test_cases: TestCaseSet, requirements: RequirementsDocument
) -> float:
    scores = []
    for tc in test_cases.test_cases:
        # Find the AC this test case references
        ac_text = _find_referenced_ac(tc, requirements)
        if ac_text:
            # Encode both and compute cosine similarity
            embeddings = model.encode([tc.gherkin.title, ac_text])
            sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            scores.append(sim)
    return sum(scores) / len(scores) if scores else 1.0
```

Thresholds:
- >= 0.8: strong consistency
- 0.6-0.8: review recommended (warning)
- < 0.6: probable hallucination / misalignment (critical warning)

**Cost:** Zero API tokens. SBERT runs locally. One-time 80MB model download. Adds ~50ms per test case for 384-dim embeddings.

### Priority 2: Enhanced Faithfulness with SBERT (est. 2h)

Supplement token-overlap faithfulness with SBERT-based semantic faithfulness:

```python
def compute_semantic_faithfulness(
    test_cases: TestCaseSet, source_doc: str
) -> float:
    source_embedding = model.encode([source_doc])
    scores = []
    for tc in test_cases.test_cases:
        grounding_embedding = model.encode([tc.grounding_source])
        sim = cosine_similarity(grounding_embedding, source_embedding)[0][0]
        scores.append(sim)
    return sum(scores) / len(scores) if scores else 1.0
```

Blend with existing lexical faithfulness: `final = 0.5 * lexical + 0.5 * semantic`

### Priority 3: Semantic Dedup (est. 1h)

Replace text-based dedup threshold with SBERT-based dedup:
```python
embeddings = model.encode([tc.gherkin.title for tc in test_cases])
# Find pairs with cosine similarity > 0.95
```

### Priority 4: Proxy-Mutation Score (est. 4h)

For each generated test case, prompt the LLM:
> "Given this test case [Gherkin], list 3 ways the implementation could be broken that this test WOULD catch, and 2 ways it could be broken that this test would MISS."

Score: `breakable_behaviors_caught / total_breakable_behaviors`

This approximates mutation score for BDD test cases without requiring executable code.

### Priority 5: Include Raw Source in Generation Prompt (est. 1h)

Add `{source_document}` alongside `{requirements_json}` in the generation prompt. Research shows docstring/context inclusion yields +19.67% branch coverage. For BDD, this means including the raw BA doc text gives the LLM more lexical anchors for faithful grounding.

---

## Updated Quality Report Specification

```
Overall Score =
  0.20 * AC Coverage
+ 0.15 * Category Balance (negative >= 20%)
+ 0.15 * Faithfulness (50% lexical + 50% SBERT semantic)
+ 0.15 * Semantic Consistency (SBERT, >= 0.80 target)
+ 0.15 * Gherkin Validity
+ 0.10 * Inferred Ratio (informational, inverse scored)
+ 0.10 * Dedup Rate
- 2 pts per duplicate (text OR semantic)
```

New metrics added: Semantic Consistency, Semantic Dedup, SBERT-enhanced Faithfulness.

## Common Pitfalls

- **Score inflation**: Unfiltered metrics inflate quality perception. TC-Bench shows curated benchmarks drop HackRate from 100% to 50%. Our duplicate detection is a step in the right direction; semantic dedup will further improve.
- **Coverage != effectiveness**: High code coverage doesn't mean tests catch bugs. For BDD, reverse-generation consistency is the best proxy.
- **Reasoning models aren't worth it**: O1 gives 3-5% more quality at 3x cost. Better prompt engineering on non-reasoning models (Gemini 2.5 Flash) is more cost-effective.
- **No single metric is sufficient**: The multi-dimensional framework is the only path to reliable quality assessment.

## Unresolved Questions

- SBERT model choice: `all-MiniLM-L6-v2` (fast, 80MB) vs `all-mpnet-base-v2` (slower, 420MB, better quality). Which balance is right?
- Should semantic consistency be a hard gate or informational metric?
- For Vietnamese BA docs, do multilingual SBERT models (`paraphrase-multilingual-MiniLM-L12-v2`) outperform English-only models on tokenized Vietnamese text?
- How to weight the proxy-mutation score in the overall quality score?

---

## Sources

- [IEEE TSE: VALTEST — Semantic Entropy for Test Validation (2026)](https://xplorestaging.ieee.org/document/11395655)
- [ICLR: TC-Bench — WrongSelect Algorithm (2026)](https://ir.hit.edu.cn/2026/0514/c19589a391875/page.htm)
- [arXiv: Farchi et al. — Reverse Generation + SBERT Validation (Nov 2025)](https://ar5iv.labs.arxiv.org/html/2511.15733)
- [ACM: MUTGEN — Mutation-Guided LLM Test Generation (2025)](https://arxiv.org/abs/2506.02954v4)
- [IEEE: Multi-Dimensional LLM Test Quality Framework (Oct 2025)](https://ieeexplore.ieee.org/abstract/document/11262355)
- [ICTSS: On Evaluation of LLM Test Suites (2025)](https://dl.acm.org/doi/10.1007/978-3-032-05188-2_16)
- [SBQS: ChatGPT vs DeepSeek Mutation Score (2025)](https://sol.sbc.org.br/index.php/sbqs/article/view/39001)
- [RAGAS Framework Docs](https://deepeval.com/docs/metrics-ragas)
- [DeepEval Faithfulness Docs](https://deepeval.com/docs/metrics-turn-faithfulness)
- [SLIIT: STEAM-LLM Framework (2025)](https://rda.sliit.lk/entities/publication/67deb878-babf-43a0-9141-404e91d073f2)
- [ODC for AI Testing (2026)](https://www.ltesting.net/wp/2026/avoiding-the-kpi-trap-in-ai-testing-quantifying-effectiveness-with-odc.html)
- [ScienceDirect: GPT-4o vs O1 vs Human QA (2025)](https://www.sciencedirect.com/science/article/abs/pii/S1568494626011567)
