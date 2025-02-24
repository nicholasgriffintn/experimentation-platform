from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .analysis_model import AnalysisConfig, MetricResult
from .enums import ExperimentStatus, ExperimentType
from .guardrails_model import GuardrailConfig
from .variants_model import VariantConfig


class ExperimentBase(BaseModel):
    name: str = Field(..., description="Name of the experiment")
    description: str = Field(..., description="Description of what the experiment is testing")
    type: ExperimentType = Field(..., description="Type of experiment")
    hypothesis: str = Field(..., description="What is being tested")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    targeting_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Rules for targeting specific users"
    )


class ExperimentSchedule(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    ramp_up_period: Optional[int] = Field(None, description="Ramp up period in hours")
    auto_stop_conditions: Optional[Dict[str, Any]] = None


class ExperimentCreate(ExperimentBase):
    variants: List[VariantConfig] = Field(..., description="Variant configurations")
    metrics: List[str] = Field(..., description="Metrics being measured")
    guardrail_metrics: Optional[List[GuardrailConfig]] = None
    schedule: Optional[ExperimentSchedule] = None
    analysis_config: Optional[AnalysisConfig] = Field(
        default_factory=lambda: AnalysisConfig(),
        description="Configuration for statistical analysis",
    )


class Experiment(ExperimentBase):
    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique identifier for the experiment"
    )
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    traffic_allocation: float = Field(
        default=100.0, description="Percentage of eligible traffic included in experiment"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    stopped_reason: Optional[str] = Field(None, description="Reason for stopping the experiment")
    variants: List[VariantConfig] = Field(
        default_factory=list, description="List of variants for this experiment"
    )
    metrics: List[str] = Field(
        default_factory=list, description="List of metric names for this experiment"
    )
    schedule: Optional[ExperimentSchedule] = Field(
        None, description="Experiment schedule configuration"
    )
    analysis_config: AnalysisConfig = Field(
        default_factory=lambda: AnalysisConfig(),
        description="Configuration for statistical analysis",
    )

    @model_validator(mode="before")
    @classmethod
    def convert_variants(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            data_dict = data.__dict__

            if "variants" in data_dict and data_dict["variants"]:
                data_dict["variants"] = [
                    {
                        "id": v.id,
                        "name": v.name,
                        "type": v.type,
                        "config": v.config,
                        "traffic_percentage": v.traffic_percentage,
                    }
                    for v in data_dict["variants"]
                ]

            if hasattr(data, "metrics"):
                data_dict["metrics"] = (
                    [metric.metric_name for metric in data.metrics] if data.metrics else []
                )

            if hasattr(data, "start_time") and data.start_time:
                data_dict["schedule"] = {
                    "start_time": data.start_time,
                    "end_time": data.end_time if hasattr(data, "end_time") else None,
                    "ramp_up_period": (
                        data.ramp_up_period if hasattr(data, "ramp_up_period") else None
                    ),
                    "auto_stop_conditions": (
                        data.auto_stop_conditions if hasattr(data, "auto_stop_conditions") else None
                    ),
                }

            if hasattr(data, "traffic_allocation"):
                data_dict["traffic_allocation"] = data.traffic_allocation
            else:
                data_dict["traffic_allocation"] = 100.0

            if "_sa_instance_state" in data_dict:
                del data_dict["_sa_instance_state"]
            return data_dict
        return data

    class Config:
        from_attributes = True
        populate_by_name = True


class ExperimentResults(BaseModel):
    experiment_id: str
    status: ExperimentStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_users: int
    metrics: Dict[str, Dict[str, MetricResult]]
    guardrail_violations: Optional[List[Dict[str, Any]]] = None
