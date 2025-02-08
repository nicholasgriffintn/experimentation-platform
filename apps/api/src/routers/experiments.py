from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime

from ..db.session import get_db
from ..services.experiments import ExperimentService
from ..models.experiment import (
    Experiment,
    ExperimentCreate,
    VariantAssignment,
    ExperimentResults,
    UserContext,
    MetricEvent,
    ExperimentSchedule,
    ExperimentStatus,
    MetricDefinition,
    ExperimentMetric
)
from ..dependencies import get_experiment_service

router = APIRouter()

@router.post("/", response_model=Experiment, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    experiment: ExperimentCreate,
    background_tasks: BackgroundTasks,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Create a new experiment"""
    for metric_name in experiment.target_metrics:
        if not await validate_metric(metric_name, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric: {metric_name}"
            )
    
    db_experiment = create_experiment_in_db(experiment, db)
    
    background_tasks.add_task(
        experiment_service.initialize_experiment,
        db_experiment.id,
        experiment.dict()
    )
    
    return db_experiment

@router.post("/{experiment_id}/assign", response_model=VariantAssignment)
async def assign_variant(
    experiment_id: str,
    user_context: UserContext,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Assign a variant to a user"""
    db_experiment = get_active_experiment(experiment_id, db)
    
    # Get variant assignment
    variant = await experiment_service.assign_variant(
        experiment_id=experiment_id,
        user_context=user_context.dict()
    )
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not meet targeting criteria"
        )
    
    return VariantAssignment(
        experiment_id=experiment_id,
        variant_id=variant.id,
        variant_name=variant.name,
        config=variant.config
    )

@router.post("/{experiment_id}/exposure")
async def record_exposure(
    experiment_id: str,
    user_context: UserContext,
    metadata: Optional[Dict] = None,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Record an exposure event"""
    db_experiment = get_active_experiment(experiment_id, db)
    
    await experiment_service.record_exposure(
        experiment_id=experiment_id,
        user_context=user_context.dict(),
        metadata=metadata
    )
    
    return {"status": "success"}

@router.post("/{experiment_id}/metric")
async def record_metric(
    experiment_id: str,
    metric_event: MetricEvent,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Record a metric event"""
    db_experiment = get_active_experiment(experiment_id, db)
    
    if not is_valid_experiment_metric(experiment_id, metric_event.metric_name, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Metric {metric_event.metric_name} is not configured for this experiment"
        )
    
    await experiment_service.record_metric(
        experiment_id=experiment_id,
        metric_name=metric_event.metric_name,
        value=metric_event.value,
        user_context=metric_event.user_context.dict(),
        metadata=metric_event.metadata
    )
    
    return {"status": "success"}

@router.get("/{experiment_id}/results", response_model=ExperimentResults)
async def get_results(
    experiment_id: str,
    metrics: Optional[List[str]] = None,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Get experiment results"""
    db_experiment = get_experiment(experiment_id, db)
    
    results = await experiment_service.analyze_results(
        experiment_id=experiment_id,
        metrics=metrics
    )
    
    return results

@router.put("/{experiment_id}/schedule")
async def update_schedule(
    experiment_id: str,
    schedule: ExperimentSchedule,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Update experiment schedule"""
    db_experiment = get_experiment(experiment_id, db)
    
    db_experiment.start_time = schedule.start_time
    db_experiment.end_time = schedule.end_time
    db.commit()
    
    await experiment_service.update_schedule(
        experiment_id=experiment_id,
        schedule=schedule.dict()
    )
    
    return {"status": "success"}

@router.post("/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str,
    reason: Optional[str] = None,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Stop an experiment"""
    db_experiment = get_active_experiment(experiment_id, db)
    
    db_experiment.status = ExperimentStatus.STOPPED
    db_experiment.ended_at = datetime.utcnow()
    db.commit()
    
    await experiment_service.stop_experiment(
        experiment_id=experiment_id,
        reason=reason
    )
    
    return {"status": "success"}

def get_experiment(experiment_id: str, db: Session) -> Experiment:
    """Get experiment or raise 404"""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    return experiment

def get_active_experiment(experiment_id: str, db: Session) -> Experiment:
    """Get running experiment or raise error"""
    experiment = get_experiment(experiment_id, db)
    if experiment.status != ExperimentStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Experiment {experiment_id} is not running"
        )
    return experiment

async def validate_metric(metric_name: str, db: Session) -> bool:
    """Validate that a metric exists"""
    metric = db.query(MetricDefinition).filter(MetricDefinition.name == metric_name).first()
    return metric is not None

def is_valid_experiment_metric(experiment_id: str, metric_name: str, db: Session) -> bool:
    """Check if metric is configured for experiment"""
    metric = db.query(ExperimentMetric).filter(
        ExperimentMetric.experiment_id == experiment_id,
        ExperimentMetric.metric_name == metric_name
    ).first()
    return metric is not None

def create_experiment_in_db(experiment: ExperimentCreate, db: Session) -> Experiment:
    """Create a new experiment in the database"""
    db_experiment = Experiment(**experiment.dict())
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment