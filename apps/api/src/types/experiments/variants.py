"""
Variant models for experiments.
"""

from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field

from ..common import VariantType


class VariantConfig(BaseModel):
    """Configuration for a variant in an experiment."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique identifier for the variant"
    )
    name: str = Field(..., description="Name of the variant")
    type: VariantType = Field(..., description="Type of variant")
    config: Dict[str, Any] = Field(default_factory=dict, description="Variant configuration")
    traffic_percentage: float = Field(
        ..., description="Percentage of traffic allocated to this variant", ge=0, le=100
    )


class VariantAssignment(BaseModel):
    """Assignment of a user to a variant in an experiment."""

    experiment_id: str
    variant_id: str
    variant_name: str
    config: Dict[str, Any]
