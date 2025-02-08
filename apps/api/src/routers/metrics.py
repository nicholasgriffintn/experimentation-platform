from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..db.session import get_db
from ..db.base import MetricDefinition as DBMetricDefinition
from ..models.experiment import MetricDefinition

router = APIRouter()

@router.post("/", response_model=MetricDefinition)
async def create_metric(metric: MetricDefinition, db: Session = Depends(get_db)):
    """Create a new metric definition"""
    db_metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric.name).first()
    if db_metric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metric {metric.name} already exists"
        )
    
    db_metric = DBMetricDefinition(
        name=metric.name,
        description=metric.description,
        unit=metric.unit,
        aggregation_method=metric.aggregation_method,
        query_template=metric.query_template
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric

@router.get("/", response_model=List[MetricDefinition])
async def list_metrics(db: Session = Depends(get_db)):
    """List all metric definitions"""
    return db.query(DBMetricDefinition).all()

@router.get("/{metric_name}", response_model=MetricDefinition)
async def get_metric(metric_name: str, db: Session = Depends(get_db)):
    """Get a specific metric by name"""
    db_metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric_name).first()
    if not db_metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric {metric_name} not found"
        )
    return db_metric

@router.delete("/{metric_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(metric_name: str, db: Session = Depends(get_db)):
    """Delete a metric"""
    db_metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric_name).first()
    if not db_metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric {metric_name} not found"
        )
    db.delete(db_metric)
    db.commit()
    return None 