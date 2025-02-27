"""
Guardrail models for experiments.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator

from ..common import GuardrailOperator


class GuardrailConfig(BaseModel):
    """Configuration for a guardrail metric in an experiment."""

    metric_name: str
    threshold: float
    operator: str = Field(..., description="Comparison operator (gt, lt, gte, lte)")


class GuardrailMetricBase(BaseModel):
    """Base model for guardrail metrics."""

    experiment_id: str
    metric_name: str
    threshold: float
    operator: GuardrailOperator
    description: Optional[str] = None

    @validator("threshold")
    def validate_threshold(cls, v: float | int) -> float:
        """Validate that the threshold is a number."""
        if not isinstance(v, (int, float)):
            raise ValueError("Threshold must be a number")
        return float(v)


class GuardrailMetricCreate(GuardrailMetricBase):
    """Model for creating a guardrail metric."""

    pass


class GuardrailMetric(GuardrailMetricBase):
    """Model for a guardrail metric."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked_at: Optional[datetime] = None
    is_violated: bool = False
    violation_count: int = 0

    class Config:
        from_attributes = True
