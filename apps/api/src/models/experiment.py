from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, computed_field, validator


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


class VariantType(str, Enum):
    CONTROL = "control"
    TREATMENT = "treatment"
    FEATURE_FLAG = "feature_flag"


class MetricType(str, Enum):
    CONTINUOUS = "continuous"
    BINARY = "binary"
    COUNT = "count"
    RATIO = "ratio"


class TargetingType(str, Enum):
    USER_ID = "user_id"
    SESSION_ID = "session_id"
    CUSTOM = "custom"


class UserContext(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class MetricEvent(BaseModel):
    metric_name: str
    value: float
    user_context: UserContext
    metadata: Optional[Dict[str, Any]] = None


class VariantConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the variant")
    name: str = Field(..., description="Name of the variant")
    type: VariantType = Field(..., description="Type of variant")
    config: Dict[str, Any] = Field(default_factory=dict, description="Variant configuration")
    traffic_percentage: float = Field(
        ..., 
        description="Percentage of traffic allocated to this variant",
        ge=0,
        le=100
    )


class MetricConfig(BaseModel):
    name: str = Field(..., description="Name of the metric")
    type: MetricType = Field(..., description="Type of metric")
    min_sample_size: int = Field(..., description="Minimum sample size required")
    min_effect_size: float = Field(..., description="Minimum detectable effect size")
    query_template: str = Field(..., description="SQL query template for calculating the metric")


class MetricDefinition(BaseModel):
    name: str = Field(..., description="Name of the metric")
    description: str = Field(..., description="Description of what the metric measures")
    unit: str = Field(..., description="Unit of measurement (e.g., '%', 'count', '$')")
    aggregation_method: str = Field(..., description="How to aggregate the metric")
    query_template: str = Field(..., description="SQL query template for calculation")

    class Config:
        from_attributes = True


class GuardrailConfig(BaseModel):
    metric_name: str
    threshold: float
    operator: str = Field(..., description="Comparison operator (gt, lt, gte, lte)")


class ExperimentSchedule(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    ramp_up_period: Optional[int] = Field(
        None, 
        description="Ramp up period in hours"
    )
    auto_stop_conditions: Optional[Dict[str, Any]] = None


class ExperimentBase(BaseModel):
    name: str = Field(..., description="Name of the experiment")
    description: str = Field(..., description="Description of what the experiment is testing")
    type: ExperimentType = Field(..., description="Type of experiment")
    hypothesis: str = Field(..., description="What is being tested")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    targeting_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Rules for targeting specific users"
    )


class ExperimentCreate(ExperimentBase):
    variants: List[VariantConfig] = Field(..., description="Variant configurations")
    target_metrics: List[str] = Field(..., description="Metrics being measured")
    guardrail_metrics: Optional[List[GuardrailConfig]] = None
    schedule: Optional[ExperimentSchedule] = None


class Experiment(ExperimentBase):
    id: str = Field(..., description="Unique identifier for the experiment")
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    @computed_field
    @property
    def target_metrics(self) -> List[str]:
        """Get the list of target metric names from the relationship."""
        return [metric.metric_name for metric in self.metrics] if hasattr(self, 'metrics') else []
    
    class Config:
        from_attributes = True


class VariantAssignment(BaseModel):
    experiment_id: str
    variant_id: str
    variant_name: str
    config: Dict[str, Any]


class MetricResult(BaseModel):
    metric_name: str
    control_mean: float
    variant_mean: float
    relative_difference: float
    p_value: float
    confidence_interval: tuple[float, float]
    sample_size: Dict[str, int]
    power: float
    is_significant: bool


class ExperimentResults(BaseModel):
    experiment_id: str
    status: ExperimentStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_users: int
    metrics: Dict[str, Dict[str, MetricResult]]  # metric_name -> variant_id -> result
    guardrail_violations: Optional[List[Dict[str, Any]]] = None

class ExperimentMetricBase(BaseModel):
    experiment_id: str
    metric_name: str

class ExperimentMetricCreate(ExperimentMetricBase):
    min_sample_size: Optional[int] = None
    min_effect_size: Optional[float] = None
    is_guardrail: bool = False
    guardrail_threshold: Optional[float] = None
    guardrail_operator: Optional[str] = None  # 'gt', 'lt', 'gte', 'lte'

class ExperimentMetric(ExperimentMetricBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
class GuardrailOperator(str, Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"

class GuardrailMetricBase(BaseModel):
    experiment_id: str
    metric_name: str
    threshold: float
    operator: GuardrailOperator
    description: Optional[str] = None

    @validator('threshold')
    def validate_threshold(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Threshold must be a number')
        return float(v)


class GuardrailMetricCreate(GuardrailMetricBase):
    pass


class GuardrailMetric(GuardrailMetricBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked_at: Optional[datetime] = None
    is_violated: bool = False
    violation_count: int = 0

    class Config:
        from_attributes = True