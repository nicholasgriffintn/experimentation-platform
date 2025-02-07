from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel

from ..db.session import get_db
from ..models.database import (
    Experiment as DBExperiment,
    MetricDefinition as DBMetricDefinition,
    ExperimentMetric
)
from ..models.experiments import Experiment, ExperimentCreate, ExperimentStatus

router = APIRouter()

class StatusUpdate(BaseModel):
    status: ExperimentStatus

@router.post("/", response_model=Experiment, status_code=status.HTTP_201_CREATED)
async def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    """Create a new experiment"""
    # Verify all target metrics exist
    for metric_name in experiment.target_metrics:
        metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric_name).first()
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Metric {metric_name} does not exist"
            )

    experiment_id = str(uuid4())
    db_experiment = DBExperiment(
        id=experiment_id,
        name=experiment.name,
        description=experiment.description,
        type=experiment.type,
        hypothesis=experiment.hypothesis,
        parameters=experiment.parameters,
        status=ExperimentStatus.DRAFT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_experiment)

    # Create metric relationships
    for metric_name in experiment.target_metrics:
        experiment_metric = ExperimentMetric(
            experiment_id=experiment_id,
            metric_name=metric_name
        )
        db.add(experiment_metric)

    db.commit()
    db.refresh(db_experiment)
    return db_experiment

@router.get("/", response_model=List[Experiment])
async def list_experiments(db: Session = Depends(get_db)):
    """List all experiments"""
    return db.query(DBExperiment).all()

@router.get("/{experiment_id}", response_model=Experiment)
async def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    """Get a specific experiment by ID"""
    db_experiment = db.query(DBExperiment).filter(DBExperiment.id == experiment_id).first()
    if not db_experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return db_experiment

@router.put("/{experiment_id}/status", response_model=Experiment)
async def update_experiment_status(
    experiment_id: str, 
    status_update: StatusUpdate,
    db: Session = Depends(get_db)
):
    """Update the status of an experiment"""
    db_experiment = db.query(DBExperiment).filter(DBExperiment.id == experiment_id).first()
    if not db_experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    
    db_experiment.status = status_update.status
    db_experiment.updated_at = datetime.utcnow()
    
    if status_update.status == ExperimentStatus.RUNNING and not db_experiment.started_at:
        db_experiment.started_at = datetime.utcnow()
    elif status_update.status in [ExperimentStatus.COMPLETED, ExperimentStatus.STOPPED] and not db_experiment.ended_at:
        db_experiment.ended_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_experiment)
    return db_experiment

@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(experiment_id: str, db: Session = Depends(get_db)):
    """Delete an experiment"""
    db_experiment = db.query(DBExperiment).filter(DBExperiment.id == experiment_id).first()
    if not db_experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    db.delete(db_experiment)
    db.commit()
    return None 