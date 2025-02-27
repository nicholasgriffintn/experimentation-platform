"""
Base models for experiments.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ..common import ExperimentType


class ExperimentBase(BaseModel):
    """Base model for experiments."""

    name: str = Field(..., description="Name of the experiment")
    description: str = Field(..., description="Description of what the experiment is testing")
    type: ExperimentType = Field(..., description="Type of experiment")
    hypothesis: Optional[str] = Field(None, description="What is being tested")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    targeting_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Rules for targeting specific users"
    )


class ExperimentSchedule(BaseModel):
    """Schedule configuration for an experiment."""

    start_time: datetime
    end_time: Optional[datetime] = None
    ramp_up_period: Optional[int] = Field(None, description="Ramp up period in hours")
    auto_stop_conditions: Optional[Dict[str, Any]] = None
