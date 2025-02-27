"""
Common enum definitions used throughout the application.
"""

from enum import Enum


class ExperimentStatus(str, Enum):
    """Status of an experiment."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ExperimentType(str, Enum):
    """Type of experiment."""

    AB_TEST = "ab_test"
    MULTIVARIATE = "multivariate"
    FEATURE_FLAG = "feature_flag"


class VariantType(str, Enum):
    """Type of variant in an experiment."""

    CONTROL = "control"
    TREATMENT = "treatment"
    FEATURE_FLAG = "feature_flag"


class TargetingType(str, Enum):
    """Type of targeting for an experiment."""

    USER_ID = "user_id"
    SESSION_ID = "session_id"
    CUSTOM = "custom"


class AnalysisMethod(str, Enum):
    """Method used for statistical analysis."""

    FREQUENTIST = "frequentist"
    BAYESIAN = "bayesian"


class CorrectionMethod(str, Enum):
    """Method used for multiple comparison correction."""

    NONE = "none"
    FDR_BH = "fdr_bh"
    HOLM = "holm"


class GuardrailOperator(str, Enum):
    """Operators used in guardrail conditions."""

    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"


class MetricType(str, Enum):
    """Type of metric."""

    CONTINUOUS = "continuous"
    BINARY = "binary"
    COUNT = "count"
    RATIO = "ratio"
