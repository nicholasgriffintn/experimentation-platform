"""
Type definitions for the experimentation platform.

This package contains all the type definitions used throughout the application,
organized in a logical structure to make them easier to find and maintain.
"""

# Analysis types
from .analysis import (
    AnalysisConfig,
    AnalysisResults,
    MetricAnalysisConfig,
    MetricResult,
)

# Common types
from .common import (
    AnalysisMethod,
    CorrectionMethod,
    ExperimentStatus,
    ExperimentType,
    GuardrailOperator,
    MetricType,
    TargetingType,
    UserContext,
    VariantType,
)

# Experiment types
from .experiments import (
    Experiment,
    ExperimentBase,
    ExperimentCreate,
    ExperimentResults,
    ExperimentSchedule,
    GuardrailConfig,
    GuardrailMetric,
    GuardrailMetricBase,
    GuardrailMetricCreate,
    VariantAssignment,
    VariantConfig,
)

# Metric types
from .metrics import (
    MetricConfig,
    MetricDefinition,
    MetricEvent,
)

__all__ = [
    # Analysis types
    "AnalysisConfig",
    "AnalysisResults",
    "MetricAnalysisConfig",
    "MetricResult",
    # Common types
    "AnalysisMethod",
    "CorrectionMethod",
    "ExperimentStatus",
    "ExperimentType",
    "GuardrailOperator",
    "MetricType",
    "TargetingType",
    "UserContext",
    "VariantType",
    # Experiment types
    "Experiment",
    "ExperimentBase",
    "ExperimentCreate",
    "ExperimentResults",
    "ExperimentSchedule",
    "GuardrailConfig",
    "GuardrailMetric",
    "GuardrailMetricBase",
    "GuardrailMetricCreate",
    "VariantAssignment",
    "VariantConfig",
    # Metric types
    "MetricConfig",
    "MetricDefinition",
    "MetricEvent",
]
