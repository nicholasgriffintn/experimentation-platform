"""
Analysis models for experiment results.
"""

from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field, model_validator

from ..common import AnalysisMethod, CorrectionMethod


class MetricAnalysisConfig(BaseModel):
    """Configuration for analyzing a specific metric."""

    min_sample_size: int = Field(default=100, gt=0)
    min_effect_size: float = Field(default=0.01, gt=0)


class AnalysisConfig(BaseModel):
    """Configuration for statistical analysis of experiments."""

    method: AnalysisMethod = Field(default=AnalysisMethod.FREQUENTIST)
    confidence_level: float = Field(default=0.95, ge=0, le=1)
    correction_method: CorrectionMethod = Field(default=CorrectionMethod.NONE)
    sequential_testing: bool = Field(default=False)
    stopping_threshold: Optional[float] = Field(default=0.01, ge=0, le=1)

    default_metric_config: MetricAnalysisConfig = Field(
        default_factory=MetricAnalysisConfig, description="Default configuration for all metrics"
    )

    metric_configs: Dict[str, MetricAnalysisConfig] = Field(
        default_factory=dict, description="Metric-specific configurations that override defaults"
    )

    prior_successes: Optional[int] = Field(default=30, ge=0)
    prior_trials: Optional[int] = Field(default=100, ge=0)
    num_samples: Optional[int] = Field(default=10000, ge=1000)

    @model_validator(mode="after")
    def validate_bayesian_params(self) -> "AnalysisConfig":
        """Validate Bayesian analysis parameters."""
        if self.method == AnalysisMethod.BAYESIAN:
            if self.prior_successes is None or self.prior_trials is None:
                raise ValueError("Bayesian analysis requires prior_successes and prior_trials")
            if self.prior_successes > self.prior_trials:
                raise ValueError("prior_successes cannot be greater than prior_trials")
        return self

    def get_metric_config(self, metric_name: str) -> MetricAnalysisConfig:
        """Get the configuration for a specific metric, falling back to defaults if not specified."""
        return self.metric_configs.get(metric_name, self.default_metric_config)


class MetricResult(BaseModel):
    """Results of analyzing a metric for an experiment."""

    metric_name: str
    control_mean: float
    variant_mean: float
    relative_difference: float
    p_value: float
    confidence_interval: Tuple[float, float]
    sample_size: Dict[str, int]
    power: float
    is_significant: bool


class AnalysisResults(BaseModel):
    """Results of analyzing an experiment."""

    experiment_id: str
    metrics: Dict[str, Dict[str, MetricResult]]
    guardrail_violations: Optional[Dict[str, Any]] = None
