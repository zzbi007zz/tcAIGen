"""UI inventory models from vision analysis (spec section 2)."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class VisionConfidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class UIElement(BaseModel):
    element_id: str
    element_type: str  # button | input | label | dropdown | table | ...
    label: Optional[str] = None
    visible_constraints: List[str] = Field(default_factory=list)
    visible_states: List[str] = Field(default_factory=list)


class Screen(BaseModel):
    screen_id: str
    screen_name: str
    source_image: Optional[str] = None
    elements: List[UIElement] = Field(default_factory=list)
    vision_confidence: VisionConfidence = VisionConfidence.medium


class UIInventory(BaseModel):
    screens: List[Screen] = Field(default_factory=list)
