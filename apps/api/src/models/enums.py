from enum import Enum

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


class TargetingType(str, Enum):
    USER_ID = "user_id"
    SESSION_ID = "session_id"
    CUSTOM = "custom"


class AnalysisMethod(str, Enum):
    FREQUENTIST = "frequentist"
    BAYESIAN = "bayesian"


class CorrectionMethod(str, Enum):
    NONE = "none"
    FDR_BH = "fdr_bh"
    HOLM = "holm"

class GuardrailOperator(str, Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"


class MetricType(str, Enum):
    CONTINUOUS = "continuous"
    BINARY = "binary"
    COUNT = "count"
    RATIO = "ratio"