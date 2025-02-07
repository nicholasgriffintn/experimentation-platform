from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .experiments import ExperimentStatus, ExperimentType


class Base(DeclarativeBase):
    pass


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(SQLEnum(ExperimentType), nullable=False)
    hypothesis: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        SQLEnum(ExperimentStatus),
        nullable=False,
        default=ExperimentStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    metrics: Mapped[List["ExperimentMetric"]] = relationship(back_populates="experiment")


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    aggregation_method: Mapped[str] = mapped_column(String, nullable=False)
    query_template: Mapped[str] = mapped_column(String, nullable=False)

    experiments: Mapped[List["ExperimentMetric"]] = relationship(back_populates="metric")


class ExperimentMetric(Base):
    __tablename__ = "experiment_metrics"

    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), primary_key=True)
    metric_name: Mapped[str] = mapped_column(ForeignKey("metric_definitions.name"), primary_key=True)

    experiment: Mapped[Experiment] = relationship(back_populates="metrics")
    metric: Mapped[MetricDefinition] = relationship(back_populates="experiments")


class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    data_type: Mapped[str] = mapped_column(String, nullable=False)
    possible_values: Mapped[list] = mapped_column(JSON, nullable=False) 