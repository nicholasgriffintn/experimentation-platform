from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from ..db.base import Experiment as DBExperiment
from ..db.base import ExperimentMetric as DBExperimentMetric
from ..db.base import FeatureDefinition as DBFeatureDefinition
from ..db.base import GuardrailMetric as DBGuardrailMetric
from ..db.base import MetricDefinition as DBMetricDefinition
from ..db.base import Variant as DBVariant
from ..db.session import get_db
from ..dependencies import get_experiment_service
from ..middleware.error_handler import ResourceNotFoundError, ValidationError
from ..models.experiments_model import Experiment as ExperimentModel
from ..models.experiments_model import (
    ExperimentCreate,
    ExperimentResults,
    ExperimentSchedule,
    ExperimentStatus,
    ExperimentType,
)
from ..models.metrics_model import MetricEvent
from ..models.user_model import UserContext
from ..models.variants_model import VariantAssignment
from ..services.experiments import ExperimentService

router = APIRouter()


@router.get("/", response_model=List[ExperimentModel])
async def list_experiments(
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> List[ExperimentModel]:
    """
    List all experiments in the system.

    Returns a list of all experiments with their configurations, variants, metrics, and current status.
    Results are ordered by creation date, with most recent experiments first.

    Returns:
        List[ExperimentModel]: A list of experiment objects with full configuration details
    """
    experiments = get_experiments_list(db)
    return [ExperimentModel.from_orm(exp) for exp in experiments]


@router.post("/", response_model=ExperimentModel, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    experiment: ExperimentCreate,
    background_tasks: BackgroundTasks,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> ExperimentModel:
    """
    Create a new experiment.

    Creates a new experiment with the specified configuration. The experiment will be initialized
    in the background and will start according to the provided schedule.

    Args:
        experiment (ExperimentCreate): The experiment configuration including name, description,
            variants, metrics, and schedule.
        background_tasks: FastAPI background tasks handler
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        ExperimentModel: The created experiment object

    Raises:
        HTTPException: 400 if invalid metrics are specified or feature validation fails
    """
    for metric_name in experiment.metrics:
        if not await validate_metric(metric_name, db):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid metric: {metric_name}"
            )

    await validate_feature_flag_experiment(experiment, db)

    db_experiment = create_experiment_in_db(experiment, db)

    background_tasks.add_task(
        experiment_service.initialize_experiment, str(db_experiment.id), experiment.dict()
    )

    return ExperimentModel.from_orm(db_experiment)


@router.get("/{experiment_id}", response_model=ExperimentModel)
async def get_experiment(
    experiment_id: str,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> ExperimentModel:
    """
    Get a specific experiment by ID.

    Retrieves detailed information about a single experiment including its configuration,
    variants, metrics, and current status.

    Args:
        experiment_id (str): The ID of the experiment to retrieve
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        ExperimentModel: The requested experiment with full configuration details

    Raises:
        ResourceNotFoundError: If experiment not found
    """
    db_experiment = get_experiment_from_db(experiment_id, db)
    return ExperimentModel.from_orm(db_experiment)


@router.post("/{experiment_id}/assign", response_model=VariantAssignment)
async def assign_variant(
    experiment_id: str,
    user_context: UserContext,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> VariantAssignment:
    """
    Assign a variant to a user.

    Deterministically assigns a variant to a user based on their context and the experiment's
    configuration. The assignment takes into account:
    - Traffic allocation
    - Targeting rules
    - Randomization seed
    - User attributes

    Args:
        experiment_id (str): The ID of the experiment
        user_context (UserContext): Context information about the user (e.g., user_id, session_id)
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        VariantAssignment: The assigned variant details including configuration

    Raises:
        ResourceNotFoundError: If experiment not found
        ValidationError: If experiment is not running
        ValidationError: If user does not meet targeting criteria
    """
    get_active_experiment(experiment_id, db)

    variant = await experiment_service.assign_variant(
        experiment_id=experiment_id, user_context=user_context.dict()
    )

    if not variant:
        raise ValidationError(
            "User does not meet targeting criteria",
            details={"experiment_id": experiment_id, "user_context": user_context.dict()},
        )

    return VariantAssignment(
        experiment_id=experiment_id,
        variant_id=str(variant.get("id")),
        variant_name=str(variant.get("name")),
        config=variant.get("config", {}),
    )


@router.post("/{experiment_id}/exposure")
async def record_exposure(
    experiment_id: str,
    user_context: UserContext,
    metadata: Optional[Dict[str, Any]] = None,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Record an exposure event for an experiment.

    Records when a user is exposed to a specific variant in an experiment. This is crucial
    for accurate experiment analysis and should be called when a user encounters the experimental feature.

    Args:
        experiment_id (str): The ID of the experiment
        user_context (UserContext): Context information about the user (e.g., user_id, session_id)
        metadata (Optional[Dict]): Additional metadata about the exposure event
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        dict: Success status

    Raises:
        ResourceNotFoundError: If experiment not found
        ValidationError: If experiment is not running
    """
    get_active_experiment(experiment_id, db)

    await experiment_service.record_exposure(
        experiment_id=experiment_id, user_context=user_context.dict(), metadata=metadata
    )

    return {"status": "success"}


@router.post("/{experiment_id}/metric")
async def record_metric(
    experiment_id: str,
    metric_event: MetricEvent,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Record a metric event for an experiment.

    Records a metric value for a user in an experiment. This endpoint should be called
    whenever a metric value is available for a user who has been exposed to the experiment.

    Args:
        experiment_id (str): The ID of the experiment
        metric_event (MetricEvent): The metric event details including:
            - metric_name: Name of the metric
            - value: The metric value
            - user_context: User context information
            - metadata: Optional additional metadata
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        dict: Success status

    Raises:
        ResourceNotFoundError: If experiment not found
        ValidationError: If experiment is not running or metric is not configured
    """
    get_active_experiment(experiment_id, db)

    if not is_valid_experiment_metric(experiment_id, metric_event.metric_name, db):
        raise ValidationError(
            f"Metric {metric_event.metric_name} is not configured for this experiment",
            details={"experiment_id": experiment_id, "metric_name": metric_event.metric_name},
        )

    await experiment_service.record_metric(
        experiment_id=experiment_id,
        metric_name=metric_event.metric_name,
        value=metric_event.value,
        user_context=metric_event.user_context.dict(),
        metadata=metric_event.metadata,
    )

    return {"status": "success"}


@router.get("/{experiment_id}/results", response_model=ExperimentResults)
async def get_results(
    experiment_id: str,
    metrics: Optional[List[str]] = None,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> ExperimentResults:
    """
    Get experiment results and analysis.

    Retrieves the current results and statistical analysis for an experiment. Results include:
    - Metric values per variant
    - Statistical significance calculations
    - Confidence intervals
    - Sample size information

    Args:
        experiment_id (str): The ID of the experiment
        metrics (Optional[List[str]]): Optional list of specific metrics to analyze. If not provided,
            all experiment metrics will be analyzed.
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        ExperimentResults: Detailed results and analysis for the experiment

    Raises:
        ResourceNotFoundError: If experiment not found
    """
    get_experiment_from_db(experiment_id, db)

    results = await experiment_service.analyze_results(experiment_id=experiment_id, metrics=metrics)

    return ExperimentResults(
        experiment_id=results["experiment_id"],
        status=results["status"],
        start_time=results["start_time"],
        end_time=results["end_time"],
        total_users=results["total_users"],
        metrics=results["metrics"],
        guardrail_violations=None,
    )


@router.put("/{experiment_id}/schedule")
async def update_schedule(
    experiment_id: str,
    schedule: ExperimentSchedule,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Update an experiment's schedule.

    Updates the scheduling configuration of an experiment, including:
    - Start and end times
    - Ramp-up period
    - Auto-stop conditions

    Args:
        experiment_id (str): The ID of the experiment
        schedule (ExperimentSchedule): The new schedule configuration including:
            - start_time: When to start the experiment
            - end_time: When to end the experiment
            - ramp_up_period: Optional gradual traffic increase period
            - auto_stop_conditions: Optional conditions for early stopping
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        dict: Success status

    Raises:
        ResourceNotFoundError: If experiment not found
    """
    db_experiment = get_experiment_from_db(experiment_id, db)

    if schedule.start_time is not None:
        db_experiment.start_time = schedule.start_time
    if schedule.end_time is not None:
        db_experiment.end_time = schedule.end_time
    if schedule.ramp_up_period is not None:
        db_experiment.ramp_up_period = schedule.ramp_up_period
    if schedule.auto_stop_conditions is not None:
        db_experiment.auto_stop_conditions = schedule.auto_stop_conditions

    db.commit()

    await experiment_service.update_schedule(
        experiment_id=experiment_id,
        schedule=schedule.model_dump(),
    )

    return {"status": "success"}


@router.post("/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str,
    reason: Optional[str] = None,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Stop an active experiment.

    Stops a running experiment and marks it as completed. This will:
    - Stop new user assignments to variants
    - Continue collecting data for already exposed users
    - Generate final results
    - Update experiment status

    Args:
        experiment_id (str): The ID of the experiment to stop
        reason (Optional[str]): Optional reason for stopping the experiment
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        dict: Success status

    Raises:
        ResourceNotFoundError: If experiment not found
        ValidationError: If experiment is not in running state
    """
    db_experiment = get_active_experiment(experiment_id, db)

    setattr(db_experiment, "status", ExperimentStatus.STOPPED)
    setattr(db_experiment, "ended_at", datetime.utcnow())
    setattr(db_experiment, "stopped_reason", reason)
    db.commit()

    await experiment_service.stop_experiment(experiment_id=experiment_id, reason=reason)

    return {"status": "success"}


@router.post("/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: str,
    reason: Optional[str] = None,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Pause a running experiment.

    Temporarily pauses a running experiment. This will:
    - Stop new user assignments to variants
    - Preserve all existing assignments
    - Continue collecting data for already exposed users
    - Allow the experiment to be resumed later

    Args:
        experiment_id (str): The ID of the experiment to pause
        reason (Optional[str]): Optional reason for pausing the experiment
        experiment_service: Injected experiment service
        db: Database session

    Returns:
        dict: Success status

    Raises:
        ResourceNotFoundError: If experiment not found
        ValidationError: If experiment is not in running state
    """
    db_experiment = get_active_experiment(experiment_id, db)

    setattr(db_experiment, "status", ExperimentStatus.PAUSED)
    db.commit()

    await experiment_service.pause_experiment(experiment_id=experiment_id, reason=reason)

    return {"status": "success"}


@router.post("/{experiment_id}/resume")
async def resume_experiment(
    experiment_id: str,
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Resume a paused experiment"""
    experiment = get_experiment_from_db(experiment_id, db)

    if experiment.status != ExperimentStatus.PAUSED:
        raise ValidationError(
            f"Experiment {experiment_id} is not paused",
            details={"experiment_id": experiment_id, "current_status": experiment.status},
        )

    setattr(experiment, "status", ExperimentStatus.RUNNING)
    db.commit()

    await experiment_service.resume_experiment(experiment_id=experiment_id)

    return {"status": "success"}


def get_experiments_list(db: Session) -> List[DBExperiment]:
    """
    Get all experiments from the database.

    Retrieves all experiments with their related entities (variants, metrics, guardrails)
    using eager loading to minimize database queries.

    Args:
        db: Database session

    Returns:
        List[DBExperiment]: List of all experiments with their related entities
    """
    print("Executing query with experiment metrics...")
    experiments = (
        db.query(DBExperiment)
        .options(
            joinedload(DBExperiment.variants),
            joinedload(DBExperiment.metrics),
            joinedload(DBExperiment.guardrail_metrics),
        )
        .all()
    )

    return experiments


def get_experiment_from_db(experiment_id: str, db: Session) -> DBExperiment:
    """
    Get a specific experiment by ID or raise 404.

    Retrieves a single experiment with its related entities using eager loading.
    Raises ResourceNotFoundError if the experiment is not found.

    Args:
        experiment_id: The ID of the experiment to retrieve
        db: Database session

    Returns:
        DBExperiment: The requested experiment with its related entities

    Raises:
        ResourceNotFoundError: If experiment not found
    """
    experiment = (
        db.query(DBExperiment)
        .options(
            joinedload(DBExperiment.variants),
            joinedload(DBExperiment.metrics),
            joinedload(DBExperiment.guardrail_metrics),
        )
        .filter(DBExperiment.id == experiment_id)
        .first()
    )

    if not experiment:
        raise ResourceNotFoundError("Experiment", experiment_id)

    return experiment


def get_active_experiment(experiment_id: str, db: Session) -> DBExperiment:
    """
    Get a running experiment or raise error.

    Retrieves an experiment and verifies it is in the running state.
    Raises appropriate errors if the experiment is not found
    or not in the running state.

    Args:
        experiment_id: The ID of the experiment to retrieve
        db: Database session

    Returns:
        DBExperiment: The requested running experiment

    Raises:
        ResourceNotFoundError: If experiment not found
        ValidationError: If experiment is not running
    """
    experiment = get_experiment_from_db(experiment_id, db)
    if experiment.status != ExperimentStatus.RUNNING:
        raise ValidationError(
            f"Experiment {experiment_id} is not running",
            details={"experiment_id": experiment_id, "current_status": experiment.status},
        )
    return experiment


async def validate_metric(metric_name: str, db: Session) -> bool:
    """Validate that a metric exists"""
    metric = db.query(DBMetricDefinition).filter(DBMetricDefinition.name == metric_name).first()
    return metric is not None


def is_valid_experiment_metric(experiment_id: str, metric_name: str, db: Session) -> bool:
    """Check if metric is configured for experiment"""
    metric = (
        db.query(DBExperimentMetric)
        .filter(
            DBExperimentMetric.experiment_id == experiment_id,
            DBExperimentMetric.metric_name == metric_name,
        )
        .first()
    )
    return metric is not None


def create_experiment_in_db(experiment: ExperimentCreate, db: Session) -> DBExperiment:
    """Create a new experiment in the database"""
    experiment_data = experiment.dict(
        exclude={
            "variants",
            "metrics",
            "guardrail_metrics",
            "schedule",
            "analysis_config",
        }
    )

    experiment_data["id"] = str(uuid4())
    experiment_data["status"] = ExperimentStatus.DRAFT

    if experiment.schedule:
        experiment_data["start_time"] = experiment.schedule.start_time
        experiment_data["end_time"] = experiment.schedule.end_time
        experiment_data["ramp_up_period"] = experiment.schedule.ramp_up_period
        if experiment.schedule.auto_stop_conditions:
            experiment_data["auto_stop_conditions"] = experiment.schedule.auto_stop_conditions

    if experiment.analysis_config:
        experiment_data["analysis_method"] = experiment.analysis_config.method
        experiment_data["confidence_level"] = experiment.analysis_config.confidence_level
        experiment_data["correction_method"] = experiment.analysis_config.correction_method
        experiment_data["sequential_testing"] = experiment.analysis_config.sequential_testing
        experiment_data["stopping_threshold"] = experiment.analysis_config.stopping_threshold
        experiment_data["prior_successes"] = experiment.analysis_config.prior_successes
        experiment_data["prior_trials"] = experiment.analysis_config.prior_trials
        experiment_data["num_samples"] = experiment.analysis_config.num_samples
        if experiment.analysis_config.default_metric_config:
            experiment_data["default_metric_config"] = (
                experiment.analysis_config.default_metric_config.model_dump()
            )

    db_experiment = DBExperiment(**experiment_data)
    db.add(db_experiment)

    for variant_data in experiment.variants:
        variant = DBVariant(
            id=variant_data.id or str(uuid4()),
            experiment_id=db_experiment.id,
            name=variant_data.name,
            type=variant_data.type.value,
            config=variant_data.config,
            traffic_percentage=variant_data.traffic_percentage,
        )
        db.add(variant)

    for metric_name in experiment.metrics:
        experiment_metric = DBExperimentMetric(
            experiment_id=db_experiment.id,
            metric_name=metric_name,
        )
        db.add(experiment_metric)

    if experiment.guardrail_metrics:
        for guardrail in experiment.guardrail_metrics:
            guardrail_metric = DBGuardrailMetric(
                experiment_id=db_experiment.id,
                metric_name=guardrail.metric_name,
                threshold=guardrail.threshold,
                operator=guardrail.operator,
            )
            db.add(guardrail_metric)

    db.commit()
    db.refresh(db_experiment)
    return db_experiment


async def validate_feature_flag_experiment(experiment: ExperimentCreate, db: Session) -> None:
    """
    Validate feature flag experiment configuration against defined features.

    Args:
        experiment: The experiment configuration
        db: Database session

    Raises:
        ValidationError: If feature validation fails
    """
    if experiment.type != ExperimentType.FEATURE_FLAG:
        return

    feature_name = experiment.parameters.get("feature_name")
    if not feature_name:
        raise ValidationError(
            "Feature flag experiments must specify feature_name in parameters",
            details={"parameters": experiment.parameters},
        )

    feature = db.query(DBFeatureDefinition).filter(DBFeatureDefinition.name == feature_name).first()
    if not feature:
        raise ValidationError(
            f"Feature {feature_name} is not defined. Create it first using the features API.",
            details={"feature_name": feature_name},
        )

    for variant in experiment.variants:
        config_value = variant.config.get("value")
        if config_value is None:
            raise ValidationError(
                f"Variant {variant.name} must specify a 'value' in config",
                details={"variant_name": variant.name, "variant_config": variant.config},
            )

        if config_value not in feature.possible_values:
            raise ValidationError(
                f"Value {config_value} for variant {variant.name} is not in allowed values for feature {feature_name}",
                details={
                    "variant_name": variant.name,
                    "value": config_value,
                    "allowed_values": feature.possible_values,
                    "feature_name": feature_name,
                },
            )
