"""Merge requirements + UI inventory; detect gaps (3 types)."""
from __future__ import annotations

import re
from typing import Dict, List, Set

from apps.api.models import (
    Feature,
    FeatureScreenMapping,
    Gap,
    GapType,
    MergeResult,
    RequirementsDocument,
    Screen,
    UIInventory,
)

MATCH_THRESHOLD = 0.2


def _tokens(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _similarity(feature: Feature, screen: Screen) -> float:
    feature_tokens = _tokens(f"{feature.name} {feature.description}")
    screen_tokens = _tokens(
        f"{screen.screen_name} " + " ".join(e.label or "" for e in screen.elements)
    )
    if not feature_tokens or not screen_tokens:
        return 0.0
    overlap = feature_tokens & screen_tokens
    return len(overlap) / len(feature_tokens | screen_tokens)


def map_features_to_screens(
    requirements: RequirementsDocument, ui_inventory: UIInventory
) -> List[FeatureScreenMapping]:
    mappings: List[FeatureScreenMapping] = []
    for feature in requirements.features:
        best_screen, best_score = None, 0.0
        for screen in ui_inventory.screens:
            score = _similarity(feature, screen)
            if score > best_score:
                best_screen, best_score = screen, score
        if best_screen is not None and best_score >= MATCH_THRESHOLD:
            mappings.append(
                FeatureScreenMapping(
                    feature_id=feature.id,
                    screen_id=best_screen.screen_id,
                    similarity_score=round(best_score, 3),
                    rationale="token overlap",
                )
            )
    return mappings


def _feature_validations(feature: Feature) -> Dict[str, Set[str]]:
    result: Dict[str, Set[str]] = {}
    for ac in feature.acceptance_criteria:
        for v in ac.validations:
            result.setdefault(v.field.lower(), set()).add(v.constraint.lower())
    return result


def detect_gaps(
    mappings: List[FeatureScreenMapping],
    requirements: RequirementsDocument,
    ui_inventory: UIInventory,
) -> List[Gap]:
    gaps: List[Gap] = []
    mapped_features = {m.feature_id for m in mappings}
    mapped_screens = {m.screen_id for m in mappings}

    for feature in requirements.features:
        if feature.id not in mapped_features:
            gaps.append(Gap(
                gap_type=GapType.requirement_without_design,
                subject_id=feature.id,
                note=f"Feature '{feature.name}' has no matching screen",
            ))
    for screen in ui_inventory.screens:
        if screen.screen_id not in mapped_screens:
            gaps.append(Gap(
                gap_type=GapType.design_without_requirement,
                subject_id=screen.screen_id,
                note=f"Screen '{screen.screen_name}' has no matching requirement",
            ))

    screens_by_id = {s.screen_id: s for s in ui_inventory.screens}
    features_by_id = {f.id: f for f in requirements.features}
    for mapping in mappings:
        feature = features_by_id.get(mapping.feature_id)
        screen = screens_by_id.get(mapping.screen_id)
        if not feature or not screen:
            continue
        validations = _feature_validations(feature)
        ui_labels = { (e.label or "").lower() for e in screen.elements }
        for field in validations:
            if any(field in label for label in ui_labels if label):
                continue  # field visible on screen; constraint compare is v2
            gaps.append(Gap(
                gap_type=GapType.validation_mismatch,
                subject_id=field,
                note=f"Validation for '{field}' in feature '{feature.name}' not visible on screen '{screen.screen_name}'",
                severity="low",
            ))
    return gaps


def merge_and_analyze(
    requirements: RequirementsDocument, ui_inventory: UIInventory
) -> MergeResult:
    mappings = map_features_to_screens(requirements, ui_inventory)
    gaps = detect_gaps(mappings, requirements, ui_inventory)
    return MergeResult(
        mappings=mappings,
        gaps=gaps,
        unmapped_features=[f.id for f in requirements.features
                           if f.id not in {m.feature_id for m in mappings}],
        unmapped_screens=[s.screen_id for s in ui_inventory.screens
                          if s.screen_id not in {m.screen_id for m in mappings}],
    )
