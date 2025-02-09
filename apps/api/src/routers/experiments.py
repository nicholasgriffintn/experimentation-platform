from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict
from datetime import datetime
from uuid import uuid4

from ..db.session import get_db
from ..services.experiments import ExperimentService
from ..models.experiment import (
    Experiment as ExperimentModel,
    ExperimentCreate,
    VariantAssignment,
    ExperimentResults,
    UserContext,
    MetricEvent,
    ExperimentSchedule,
    ExperimentStatus,
)
from ..db.base import (
    Experiment as DBExperiment,
    MetricDefinition as DBMetricDefinition,
    ExperimentMetric as DBExperimentMetric,
    Variant as DBVariant
)
from ..dependencies import get_experiment_service

router = APIRouter()

@router.get("/", response_model=List[ExperimentModel])
async def list_experiments(
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """List all experiments"""
    experiments = get_experiments_list(db)
    return experiments

@router.post("/", response_model=ExperimentModel, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    experiment: ExperimentCreate,
    background_tasks: BackgroundTasks,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Create a new experiment"""
    for metric_name in experiment.metrics:
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

@router.get("/{experiment_id}", response_model=ExperimentModel)
async def get_experiment(
    experiment_id: str,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Get an experiment"""
    return get_experiment(experiment_id, db)

@router.post("/{experiment_id}/assign", response_model=VariantAssignment)
async def assign_variant(
    experiment_id: str,
    user_context: UserContext,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
):
    """Assign a variant to a user"""
    db_experiment = get_active_experiment(experiment_id, db)
    
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
    db_experiment.stopped_reason = reason
    db.commit()
    
    await experiment_service.stop_experiment(
        experiment_id=experiment_id,
        reason=reason
    )
    
    return {"status": "success"}

def get_experiments_list(db: Session) -> List[DBExperiment]:
    """Get all experiments"""
    print("Executing query with experiment metrics...")
    experiments = db.query(DBExperiment).options(
        joinedload(DBExperiment.variants),
        joinedload(DBExperiment.metrics),
        joinedload(DBExperiment.guardrail_metrics)
    ).all()
    
    
    return experiments

def get_experiment(experiment_id: str, db: Session) -> DBExperiment:
    """Get experiment or raise 404"""
    experiment = db.query(DBExperiment).options(
        joinedload(DBExperiment.variants),
        joinedload(DBExperiment.metrics),
        joinedload(DBExperiment.guardrail_metrics)
    ).filter(DBExperiment.id == experiment_id).first()
    
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found"
        )
    
    return experiment

def get_active_experiment(experiment_id: str, db: Session) -> DBExperiment:
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
    metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric_name).first()
    return metric is not None

def is_valid_experiment_metric(experiment_id: str, metric_name: str, db: Session) -> bool:
    """Check if metric is configured for experiment"""
    metric = db.query(DBExperimentMetric).filter(
        DBExperimentMetric.experiment_id == experiment_id,
        DBExperimentMetric.metric_name == metric_name
    ).first()
    return metric is not None

def create_experiment_in_db(experiment: ExperimentCreate, db: Session) -> DBExperiment:
    """Create a new experiment in the database"""
    experiment_data = experiment.dict(
        exclude={
            'variants',
            'metrics',
            'guardrail_metrics',
            'metrics',
            'schedule'
        }
    )
    
    experiment_data['id'] = str(uuid4())
    experiment_data['status'] = ExperimentStatus.DRAFT
    
    if experiment.schedule:
        experiment_data['start_time'] = experiment.schedule.start_time
        experiment_data['end_time'] = experiment.schedule.end_time
    
    db_experiment = DBExperiment(**experiment_data)
    db.add(db_experiment)
    
    for variant_data in experiment.variants:
        variant = DBVariant(
            id=variant_data.id or str(uuid4()),
            experiment_id=db_experiment.id,
            name=variant_data.name,
            type=variant_data.type.value,
            config=variant_data.config,
            traffic_percentage=variant_data.traffic_percentage
        )
        db.add(variant)
    
    for metric_name in experiment.metrics:
        experiment_metric = DBExperimentMetric(
            experiment_id=db_experiment.id,
            metric_name=metric_name
        )
        db.add(experiment_metric)
    
    db.commit()
    db.refresh(db_experiment)
    return db_experiment