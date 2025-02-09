from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, model_validator
from uuid import uuid4


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
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the variant")
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
    data_type: MetricType = Field(..., description="Type of metric (continuous, binary, count, ratio)")
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


class AnalysisMethod(str, Enum):
    FREQUENTIST = "frequentist"
    BAYESIAN = "bayesian"


class CorrectionMethod(str, Enum):
    NONE = "none"
    FDR_BH = "fdr_bh"
    HOLM = "holm"


class MetricAnalysisConfig(BaseModel):
    min_sample_size: int = Field(default=100, gt=0)
    min_effect_size: float = Field(default=0.01, gt=0)


class AnalysisConfig(BaseModel):
    method: AnalysisMethod = Field(default=AnalysisMethod.FREQUENTIST)
    confidence_level: float = Field(default=0.95, ge=0, le=1)
    correction_method: CorrectionMethod = Field(default=CorrectionMethod.NONE)
    sequential_testing: bool = Field(default=False)
    stopping_threshold: Optional[float] = Field(default=0.01, ge=0, le=1)
    
    default_metric_config: MetricAnalysisConfig = Field(
        default_factory=MetricAnalysisConfig,
        description="Default configuration for all metrics"
    )
    
    metric_configs: Dict[str, MetricAnalysisConfig] = Field(
        default_factory=dict,
        description="Metric-specific configurations that override defaults"
    )
    
    prior_successes: Optional[int] = Field(default=30, ge=0)
    prior_trials: Optional[int] = Field(default=100, ge=0)
    num_samples: Optional[int] = Field(default=10000, ge=1000)

    @model_validator(mode='after')
    def validate_bayesian_params(self):
        if self.method == AnalysisMethod.BAYESIAN:
            if self.prior_successes is None or self.prior_trials is None:
                raise ValueError("Bayesian analysis requires prior_successes and prior_trials")
            if self.prior_successes > self.prior_trials:
                raise ValueError("prior_successes cannot be greater than prior_trials")
        return self

    def get_metric_config(self, metric_name: str) -> MetricAnalysisConfig:
        """Get the configuration for a specific metric, falling back to defaults if not specified"""
        return self.metric_configs.get(metric_name, self.default_metric_config)


class ExperimentCreate(ExperimentBase):
    variants: List[VariantConfig] = Field(..., description="Variant configurations")
    metrics: List[str] = Field(..., description="Metrics being measured")
    guardrail_metrics: Optional[List[GuardrailConfig]] = None
    schedule: Optional[ExperimentSchedule] = None
    analysis_config: Optional[AnalysisConfig] = Field(
        default_factory=lambda: AnalysisConfig(),
        description="Configuration for statistical analysis"
    )


class Experiment(ExperimentBase):
    id: str = Field(..., description="Unique identifier for the experiment")
    status: ExperimentStatus = Field(default=ExperimentStatus.DRAFT)
    traffic_allocation: float = Field(default=100.0, description="Percentage of eligible traffic included in experiment")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    stopped_reason: Optional[str] = Field(None, description="Reason for stopping the experiment")
    variants: List[VariantConfig] = Field(default_factory=list, description="List of variants for this experiment")
    metrics: List[str] = Field(default_factory=list, description="List of metric names for this experiment")
    schedule: Optional[ExperimentSchedule] = Field(None, description="Experiment schedule configuration")
    analysis_config: AnalysisConfig = Field(
        default_factory=lambda: AnalysisConfig(),
        description="Configuration for statistical analysis"
    )
    
    @model_validator(mode='before')
    @classmethod
    def convert_variants(cls, data: Any) -> Any:
        if hasattr(data, '__dict__'):
            data_dict = data.__dict__
            print(f"Model validator:")
            print(f"  Original data type: {type(data)}")
            print(f"  Original data dict: {data_dict}")
            
            if 'variants' in data_dict and data_dict['variants']:
                data_dict['variants'] = [
                    {
                        'id': v.id,
                        'name': v.name,
                        'type': v.type,
                        'config': v.config,
                        'traffic_percentage': v.traffic_percentage
                    }
                    for v in data_dict['variants']
                ]
            
            if hasattr(data, 'metrics'):
                print(f"  Found metrics: {data.metrics}")
                data_dict['metrics'] = [metric.metric_name for metric in data.metrics] if data.metrics else []
            
            if hasattr(data, 'start_time') and data.start_time:
                data_dict['schedule'] = {
                    'start_time': data.start_time,
                    'end_time': data.end_time if hasattr(data, 'end_time') else None,
                    'ramp_up_period': data.ramp_up_period if hasattr(data, 'ramp_up_period') else None,
                    'auto_stop_conditions': data.auto_stop_conditions if hasattr(data, 'auto_stop_conditions') else None
                }

            if hasattr(data, 'traffic_allocation'):
                data_dict['traffic_allocation'] = data.traffic_allocation
            else:
                data_dict['traffic_allocation'] = 100.0
            
            if '_sa_instance_state' in data_dict:
                del data_dict['_sa_instance_state']
            return data_dict
        return data
    
    class Config:
        from_attributes = True
        populate_by_name = True


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