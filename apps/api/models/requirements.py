"""Requirements document models (spec section 1)."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class SourceType(str, Enum):
    word = "word"
    pdf = "pdf"
    paste = "paste"


class Grounding(str, Enum):
    explicit = "explicit"
    inferred = "inferred"


class DocumentMeta(BaseModel):
    title: str
    source_type: SourceType
    author: Optional[str] = None
    version: Optional[str] = None
    date: Optional[str] = None


class InputValidation(BaseModel):
    field: str
    constraint: str
    error_message: Optional[str] = None
    grounding: Grounding = Grounding.explicit


class AcceptanceCriterion(BaseModel):
    id: str
    text: str
    grounding: Grounding = Grounding.explicit
    source_location: str
    validations: List[InputValidation] = Field(default_factory=list)


class Feature(BaseModel):
    id: str
    name: str
    description: str
    source_location: str
    acceptance_criteria: List[AcceptanceCriterion] = Field(default_factory=list)


class ExtractionConfidence(BaseModel):
    explicit_criteria_count: int = 0
    inferred_criteria_count: int = 0
    low_confidence_features: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def counts_non_negative(self) -> "ExtractionConfidence":
        if self.explicit_criteria_count < 0 or self.inferred_criteria_count < 0:
            raise ValueError("criteria counts must be non-negative")
        return self

    @property
    def total_criteria(self) -> int:
        return self.explicit_criteria_count + self.inferred_criteria_count


class RequirementsDocument(BaseModel):
    meta: DocumentMeta
    features: List[Feature] = Field(default_factory=list)
    confidence: ExtractionConfidence = Field(default_factory=ExtractionConfidence)
