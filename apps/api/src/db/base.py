from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..models.analysis_model import AnalysisMethod, CorrectionMethod
from ..models.experiments_model import (
    ExperimentStatus,
    ExperimentType,
)


class Base(DeclarativeBase):
    pass


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    type: Mapped[ExperimentType] = mapped_column(SQLEnum(ExperimentType), nullable=False)
    hypothesis: Mapped[str | None] = mapped_column(String)
    targeting_rules: Mapped[dict] = mapped_column(JSON, default={})
    parameters: Mapped[dict] = mapped_column(JSON, default={})
    status: Mapped[ExperimentStatus] = mapped_column(SQLEnum(ExperimentStatus), nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    ramp_up_period: Mapped[int | None] = mapped_column(Integer, nullable=True)  # in hours
    auto_stop_conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    traffic_allocation: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    stopped_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    analysis_method: Mapped[AnalysisMethod] = mapped_column(
        SQLEnum(AnalysisMethod), nullable=False, default=AnalysisMethod.FREQUENTIST
    )
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    correction_method: Mapped[CorrectionMethod] = mapped_column(
        SQLEnum(CorrectionMethod), nullable=False, default=CorrectionMethod.NONE
    )
    sequential_testing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stopping_threshold: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.01)

    metric_configs: Mapped[dict] = mapped_column(JSON, default={})
    default_metric_config: Mapped[dict] = mapped_column(
        JSON, nullable=False, default={"min_sample_size": 100, "min_effect_size": 0.01}
    )

    prior_successes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=30)
    prior_trials: Mapped[int | None] = mapped_column(Integer, nullable=True, default=100)
    num_samples: Mapped[int | None] = mapped_column(Integer, nullable=True, default=10000)

    variants: Mapped[list["Variant"]] = relationship("Variant", back_populates="experiment")
    metrics: Mapped[list["ExperimentMetric"]] = relationship(
        "ExperimentMetric", back_populates="experiment"
    )
    guardrail_metrics: Mapped[list["GuardrailMetric"]] = relationship(
        "GuardrailMetric", back_populates="experiment"
    )


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    experiment_id: Mapped[str] = mapped_column(String, ForeignKey("experiments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # control, treatment, feature_flag
    config: Mapped[dict] = mapped_column(JSON, default={})
    traffic_percentage: Mapped[float] = mapped_column(Float, nullable=False)

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="variants")
    assignments: Mapped[list["Assignment"]] = relationship("Assignment", back_populates="variant")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    experiment_id: Mapped[str] = mapped_column(String, ForeignKey("experiments.id"), nullable=False)
    variant_id: Mapped[str] = mapped_column(String, ForeignKey("variants.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    variant: Mapped["Variant"] = relationship("Variant", back_populates="assignments")


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str | None] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    data_type: Mapped[str] = mapped_column(String, nullable=False)  # continuous, binary, count
    aggregation_method: Mapped[str] = mapped_column(String, nullable=False)
    query_template: Mapped[str | None] = mapped_column(String)


class ExperimentMetric(Base):
    __tablename__ = "experiment_metrics"

    experiment_id: Mapped[str] = mapped_column(
        String, ForeignKey("experiments.id"), primary_key=True
    )
    metric_name: Mapped[str] = mapped_column(
        String, ForeignKey("metric_definitions.name"), primary_key=True
    )

    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="metrics")
    metric: Mapped["MetricDefinition"] = relationship("MetricDefinition")


class GuardrailMetric(Base):
    __tablename__ = "guardrail_metrics"

    experiment_id: Mapped[str] = mapped_column(
        String, ForeignKey("experiments.id"), primary_key=True
    )
    metric_name: Mapped[str] = mapped_column(
        String, ForeignKey("metric_definitions.name"), primary_key=True
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    operator: Mapped[str] = mapped_column(String, nullable=False)  # gt, lt, gte, lte

    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="guardrail_metrics"
    )
    metric: Mapped["MetricDefinition"] = relationship("MetricDefinition")


class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[str] = mapped_column(String, nullable=False)
    possible_values: Mapped[list] = mapped_column(JSON, nullable=False)
