"""Verifier verdict and loop budget models."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class FailedCriterion(BaseModel):
    criterion: str
    reason: str
    tc_id: Optional[str] = None


class VerifierVerdict(BaseModel):
    passed: bool
    confidence: float = 1.0
    failed_criteria: List[FailedCriterion] = Field(default_factory=list)
    feedback: Optional[str] = None
    model: Optional[str] = None


class GateResult(BaseModel):
    passed: bool
    gherkin_pass: bool = True
    dup_count: int = 0
    errors: List[str] = Field(default_factory=list)


class LoopBudget(BaseModel):
    max_iterations: int = 3
    max_usd: float = 0.50
    cost_per_iteration: float = 0.03
    no_progress_stop: bool = True


class LoopResult(BaseModel):
    passed: bool
    actual_iterations: int = 0
    total_cost: float = 0.0
    final_output: Optional[dict] = None
    verdicts: List[VerifierVerdict] = Field(default_factory=list)
