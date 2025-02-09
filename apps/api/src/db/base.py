from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, ForeignKey, Float, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..models.experiment import (
    ExperimentStatus,
    ExperimentType,
    AnalysisMethod,
    CorrectionMethod
)


class Base(DeclarativeBase):
    pass


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(SQLEnum(ExperimentType), nullable=False)
    hypothesis = Column(String)
    targeting_rules = Column(JSON, default={})
    parameters = Column(JSON, default={})
    status = Column(SQLEnum(ExperimentStatus), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    ramp_up_period = Column(Integer, nullable=True)  # in hours
    auto_stop_conditions = Column(JSON, nullable=True)
    traffic_allocation = Column(Float, nullable=False, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    stopped_reason = Column(String, nullable=True)
    
    analysis_method = Column(SQLEnum(AnalysisMethod), nullable=False, default=AnalysisMethod.FREQUENTIST)
    confidence_level = Column(Float, nullable=False, default=0.95)
    correction_method = Column(SQLEnum(CorrectionMethod), nullable=False, default=CorrectionMethod.NONE)
    sequential_testing = Column(Boolean, nullable=False, default=False)
    stopping_threshold = Column(Float, nullable=True, default=0.01)
    
    metric_configs = Column(JSON, default={})
    default_metric_config = Column(JSON, nullable=False, default={
        "min_sample_size": 100,
        "min_effect_size": 0.01
    })
    
    prior_successes = Column(Integer, nullable=True, default=30)
    prior_trials = Column(Integer, nullable=True, default=100)
    num_samples = Column(Integer, nullable=True, default=10000)
    
    variants = relationship("Variant", back_populates="experiment")
    metrics = relationship("ExperimentMetric", back_populates="experiment")
    guardrail_metrics = relationship("GuardrailMetric", back_populates="experiment")

class Variant(Base):
    __tablename__ = "variants"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # control, treatment, feature_flag
    config = Column(JSON, default={})
    traffic_percentage = Column(Float, nullable=False)
    
    experiment = relationship("Experiment", back_populates="variants")
    assignments = relationship("Assignment", back_populates="variant")

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False)
    variant_id = Column(String, ForeignKey("variants.id"), nullable=False)
    user_id = Column(String, nullable=False)
    context = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    variant = relationship("Variant", back_populates="assignments")

class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    name = Column(String, primary_key=True)
    description = Column(String)
    unit = Column(String)
    data_type = Column(String, nullable=False)  # continuous, binary, count
    aggregation_method = Column(String, nullable=False)
    query_template = Column(String)

class ExperimentMetric(Base):
    __tablename__ = "experiment_metrics"

    experiment_id = Column(String, ForeignKey("experiments.id"), primary_key=True)
    metric_name = Column(String, ForeignKey("metric_definitions.name"), primary_key=True)
    
    experiment = relationship("Experiment", back_populates="metrics")
    metric = relationship("MetricDefinition")

class GuardrailMetric(Base):
    __tablename__ = "guardrail_metrics"

    experiment_id = Column(String, ForeignKey("experiments.id"), primary_key=True)
    metric_name = Column(String, ForeignKey("metric_definitions.name"), primary_key=True)
    threshold = Column(Float, nullable=False)
    operator = Column(String, nullable=False)  # gt, lt, gte, lte
    
    experiment = relationship("Experiment", back_populates="guardrail_metrics")
    metric = relationship("MetricDefinition")

class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[str] = mapped_column(String, nullable=False)
    possible_values: Mapped[list] = mapped_column(JSON, nullable=False) 