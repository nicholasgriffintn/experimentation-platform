from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .enums import MetricType
from .user_model import UserContext


class MetricEvent(BaseModel):
    metric_name: str
    value: float
    user_context: UserContext
    metadata: Optional[Dict[str, Any]] = None


class MetricDefinition(BaseModel):
    name: str = Field(..., description="Name of the metric")
    description: Optional[str] = Field(None, description="Description of what the metric measures")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., '%', 'count', '$')")
    data_type: MetricType = Field(
        ..., description="Type of metric (continuous, binary, count, ratio)"
    )
    aggregation_method: str = Field(..., description="How to aggregate the metric")
    query_template: Optional[str] = Field(None, description="SQL query template for calculation")

    class Config:
        from_attributes = True


class MetricConfig(BaseModel):
    name: str = Field(..., description="Name of the metric")
    type: MetricType = Field(..., description="Type of metric")
    min_sample_size: int = Field(..., description="Minimum sample size required")
    min_effect_size: float = Field(..., description="Minimum detectable effect size")
    query_template: str = Field(..., description="SQL query template for calculating the metric")
