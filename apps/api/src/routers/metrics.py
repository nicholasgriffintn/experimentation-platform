from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.base import MetricDefinition as DBMetricDefinition
from ..db.session import get_db
from ..middleware.error_handler import ResourceNotFoundError, ValidationError
from ..types import MetricDefinition, MetricType

router = APIRouter()


@router.post("/", response_model=MetricDefinition)
async def create_metric(
    metric: MetricDefinition, db: Session = Depends(get_db)
) -> MetricDefinition:
    """
    Create a new metric definition.

    Creates a new metric that can be used in experiments. The metric definition includes:
    - How the metric is calculated
    - What type of data it represents
    - How it should be aggregated
    - The SQL query template for data collection

    Args:
        metric (MetricDefinition): The metric configuration including name, description,
            data type, and aggregation method
        db: Database session

    Returns:
        MetricDefinition: The created metric definition

    Raises:
        ValidationError: If metric with same name already exists
    """
    db_metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric.name).first()
    if db_metric:
        raise ValidationError(
            f"Metric {metric.name} already exists", details={"metric_name": metric.name}
        )

    db_metric = DBMetricDefinition(
        name=metric.name,
        description=metric.description,
        unit=metric.unit,
        data_type=metric.data_type.value,
        aggregation_method=metric.aggregation_method,
        query_template=metric.query_template,
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return MetricDefinition(
        name=db_metric.name,
        description=db_metric.description,
        unit=db_metric.unit,
        data_type=MetricType(db_metric.data_type),
        aggregation_method=db_metric.aggregation_method,
        query_template=db_metric.query_template,
    )


@router.get("/", response_model=List[MetricDefinition])
async def list_metrics(db: Session = Depends(get_db)) -> List[MetricDefinition]:
    """
    List all metric definitions.

    Returns a list of all available metrics that can be used in experiments.

    Args:
        db: Database session

    Returns:
        List[MetricDefinition]: List of all metric definitions
    """
    db_metrics = db.query(DBMetricDefinition).all()
    return [
        MetricDefinition(
            name=m.name,
            description=m.description,
            unit=m.unit,
            data_type=MetricType(m.data_type),
            aggregation_method=m.aggregation_method,
            query_template=m.query_template,
        )
        for m in db_metrics
    ]


@router.get("/{metric_name}", response_model=MetricDefinition)
async def get_metric(metric_name: str, db: Session = Depends(get_db)) -> MetricDefinition:
    """
    Get a specific metric definition.

    Args:
        metric_name (str): The name of the metric to retrieve
        db: Database session

    Returns:
        MetricDefinition: The requested metric definition

    Raises:
        ResourceNotFoundError: If metric not found
    """
    metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric_name).first()
    if not metric:
        raise ResourceNotFoundError("Metric", metric_name)
    return MetricDefinition(
        name=metric.name,
        description=metric.description,
        unit=metric.unit,
        data_type=MetricType(metric.data_type),
        aggregation_method=metric.aggregation_method,
        query_template=metric.query_template,
    )


@router.delete("/{metric_name}", status_code=204)
async def delete_metric(metric_name: str, db: Session = Depends(get_db)) -> None:
    """
    Delete a metric definition.

    Args:
        metric_name (str): The name of the metric to delete
        db: Database session

    Raises:
        ResourceNotFoundError: If metric not found
    """
    metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric_name).first()
    if not metric:
        raise ResourceNotFoundError("Metric", metric_name)

    db.delete(metric)
    db.commit()
