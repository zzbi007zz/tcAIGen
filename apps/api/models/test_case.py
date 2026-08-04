"""Test case models with Gherkin output (spec section 4)."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    scenario = "scenario"
    scenario_outline = "scenario_outline"


class Category(str, Enum):
    positive = "positive"
    negative = "negative"
    edge = "edge"
    boundary = "boundary"


class TestStep(BaseModel):
    keyword: str  # Given | When | Then | And | But
    text: str


class Gherkin(BaseModel):
    scenario_type: ScenarioType = ScenarioType.scenario
    title: str
    steps: List[TestStep] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    examples_table: Optional[List[Dict[str, str]]] = None


class TestCase(BaseModel):
    tc_id: str
    feature_id: str
    title: str
    category: Category = Category.positive
    priority: str = "medium"
    grounding_source: str  # mandatory — cite original doc text
    gherkin: Gherkin


class TestCaseSet(BaseModel):
    source_doc_title: Optional[str] = None
    test_cases: List[TestCase] = Field(default_factory=list)
