"""SBERT-based semantic metrics: consistency, faithfulness, dedup.

Uses a lazy-loaded local Sentence-BERT model (all-MiniLM-L6-v2) so all
metrics run locally with zero API cost. Every public function degrades
gracefully (returns None / empty) when sentence-transformers or the model
is unavailable.
"""
from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from apps.api.models import RequirementsDocument, TestCase, TestCaseSet

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
SEMANTIC_DUP_THRESHOLD = 0.95

_model = None


def _get_model():
    """Lazy singleton: load the SBERT model once, reuse across metrics."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _encode(texts: List[str]):
    model = _get_model()
    return model.encode(texts, convert_to_tensor=True)


def _cosine(a, b) -> float:
    denom = float(a.norm() * b.norm())
    return float(a @ b) / denom if denom else 0.0


def _tc_text(tc: TestCase) -> str:
    steps = " ".join(step.text for step in tc.gherkin.steps)
    return f"{tc.title} {tc.gherkin.title} {steps}".strip()


def _strip_inferred_tag(text: str) -> str:
    return re.sub(r"\s*\(inferred\)\s*$", "", text.strip(), flags=re.IGNORECASE)


def _find_ac(tc: TestCase, requirements: RequirementsDocument) -> Optional[str]:
    """Find the acceptance criterion text cited by tc.grounding_source."""
    grounding = _strip_inferred_tag(tc.grounding_source).lower()
    if not grounding:
        return None
    best_text, best_ratio = None, 0.0
    for feature in requirements.features:
        for ac in feature.acceptance_criteria:
            ratio = SequenceMatcher(None, grounding, ac.text.lower()).ratio()
            if ratio > best_ratio:
                best_text, best_ratio = ac.text, ratio
    return best_text if best_ratio >= 0.4 else None


def _tc_payload(tc: TestCase) -> str:
    steps = " ".join(step.text for step in tc.gherkin.steps)
    return f"{tc.gherkin.title} {steps}".strip()


def compute_semantic_consistency(
    test_cases: TestCaseSet, requirements: RequirementsDocument
) -> Optional[float]:
    """Average SBERT cosine similarity between each TC and its cited AC.

    Returns None when SBERT is unavailable or no TC can be mapped to an AC.
    """
    if not test_cases.test_cases:
        return None
    try:
        pairs: List[Tuple[str, str]] = []
        for tc in test_cases.test_cases:
            ac_text = _find_ac(tc, requirements)
            if ac_text:
                pairs.append((_tc_payload(tc), ac_text))
        if not pairs:
            return None
        left = _encode([p[0] for p in pairs])
        right = _encode([p[1] for p in pairs])
        scores = [_cosine(left[i], right[i]) for i in range(len(pairs))]
        return sum(scores) / len(scores)
    except Exception as exc:
        logger.warning("semantic consistency unavailable: %s", exc)
        return None


def compute_semantic_faithfulness(
    test_cases: TestCaseSet, source_doc: str
) -> Optional[float]:
    """Average SBERT cosine similarity of grounding_source vs source doc chunks.

    Returns None when SBERT is unavailable or inputs are empty.
    """
    if not test_cases.test_cases or not source_doc.strip():
        return None
    groundings = [tc.grounding_source.strip() for tc in test_cases.test_cases]
    if not any(groundings):
        return None
    try:
        chunks = [c.strip() for c in re.split(r"\n+", source_doc) if c.strip()]
        if not chunks:
            return None
        chunk_emb = _encode(chunks)
        non_empty = [g for g in groundings if g]
        grounding_emb = _encode(non_empty)
        scores: List[float] = [0.0] * (len(groundings) - len(non_empty))
        for emb in grounding_emb:
            best = max(_cosine(emb, chunk) for chunk in chunk_emb)
            scores.append(best)
        return sum(scores) / len(scores)
    except Exception as exc:
        logger.warning("semantic faithfulness unavailable: %s", exc)
        return None


def detect_semantic_duplicates(
    test_cases: TestCaseSet, threshold: float = SEMANTIC_DUP_THRESHOLD
) -> List[Tuple[str, str]]:
    """Pairs of test cases whose SBERT title similarity >= threshold."""
    cases = test_cases.test_cases
    if len(cases) < 2:
        return []
    try:
        embeddings = _encode([_tc_text(tc) for tc in cases])
        pairs: List[Tuple[str, str]] = []
        for i in range(len(cases)):
            for j in range(i + 1, len(cases)):
                if _cosine(embeddings[i], embeddings[j]) >= threshold:
                    pairs.append((cases[i].tc_id, cases[j].tc_id))
        return pairs
    except Exception as exc:
        logger.warning("semantic dedup unavailable: %s", exc)
        return []
