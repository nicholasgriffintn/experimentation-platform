from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, computed_field


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ExperimentType(str, Enum):
    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    FEATURE_FLAG = "feature_flag"


class MetricDefinition(BaseModel):
    name: str = Field(..., description="Name of the metric")
    description: str = Field(..., description="Description of what the metric measures")
    unit: str = Field(..., description="Unit of measurement (e.g., '%', 'count', '$')")
    aggregation_method: str = Field(..., description="How to aggregate the metric (sum, average, count, ratio)")
    query_template: str = Field(..., description="SQL query template for calculating the metric")

    class Config:
        from_attributes = True


class ExperimentBase(BaseModel):
    name: str = Field(..., description="Name of the experiment")
    description: str = Field(..., description="Description of what the experiment is testing")
    type: ExperimentType = Field(..., description="Type of experiment")
    hypothesis: str = Field(..., description="What is being tested")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Experiment parameters")


class ExperimentCreate(ExperimentBase):
    target_metrics: List[str] = Field(..., description="Metrics being measured")


class Experiment(ExperimentBase):
    id: str = Field(..., description="Unique identifier for the experiment")
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)
    
    @computed_field
    @property
    def target_metrics(self) -> List[str]:
        """Get the list of target metric names from the relationship."""
        return [metric.metric_name for metric in self.metrics] if hasattr(self, 'metrics') else []
    
    class Config:
        from_attributes = True 