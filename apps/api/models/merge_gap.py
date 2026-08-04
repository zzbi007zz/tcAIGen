"""Feature-screen mapping and gap models (spec section 3)."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class GapType(str, Enum):
    requirement_without_design = "requirement_without_design"
    design_without_requirement = "design_without_requirement"
    validation_mismatch = "validation_mismatch"


class FeatureScreenMapping(BaseModel):
    feature_id: str
    screen_id: str
    similarity_score: float = 0.0
    rationale: Optional[str] = None


class Gap(BaseModel):
    gap_type: GapType
    subject_id: str  # feature_id, screen_id, or field name
    note: str
    severity: str = "medium"  # low | medium | high


class MergeResult(BaseModel):
    mappings: List[FeatureScreenMapping] = Field(default_factory=list)
    gaps: List[Gap] = Field(default_factory=list)
    unmapped_features: List[str] = Field(default_factory=list)
    unmapped_screens: List[str] = Field(default_factory=list)
