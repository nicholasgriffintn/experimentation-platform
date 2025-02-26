from datetime import datetime, timedelta
from typing import List, TypedDict
from uuid import uuid4

from sqlalchemy.orm import Session

from ..config.app import settings
from ..models.analysis_model import AnalysisMethod, CorrectionMethod
from ..models.experiments_model import ExperimentStatus, ExperimentType
from ..models.guardrails_model import GuardrailOperator
from ..models.variants_model import VariantType
from ..services.data import DataService
from ..utils.logger import logger
from .base import Experiment as DBExperiment
from .base import ExperimentMetric, FeatureDefinition, GuardrailMetric, MetricDefinition
from .base import Variant as DBVariant


def get_data_service(
    metadata_db: Session
) -> DataService:
    """Get initialized data service instance."""
    return DataService(
        metadata_db=metadata_db,
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        user=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


class MetricSeed(TypedDict):
    """Metric seed data."""

    name: str
    description: str
    unit: str
    data_type: str
    aggregation_method: str
    query_template: str


class FeatureSeed(TypedDict):
    """Feature seed data."""

    name: str
    description: str
    data_type: str
    possible_values: List[str]


def seed_metrics(db: Session) -> None:
    """Seed metric definitions."""
    metrics: List[MetricSeed] = [
        {
            "name": "conversion_rate",
            "description": "Percentage of users who complete a desired action",
            "unit": "percentage",
            "data_type": "binary",
            "aggregation_method": "mean",
            "query_template": """
            SELECT
                variant_id,
                COUNT(DISTINCT CASE WHEN event_type = 'conversion' THEN user_id END) / COUNT(DISTINCT user_id) AS value
            FROM {experiment_id}_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY variant_id
            """,
        },
        {
            "name": "revenue_per_user",
            "description": "Average revenue generated per user",
            "unit": "currency",
            "data_type": "continuous",
            "aggregation_method": "mean",
            "query_template": """
            SELECT
                variant_id,
                SUM(event_value) / COUNT(DISTINCT user_id) AS value
            FROM {experiment_id}_events
            WHERE event_type = 'purchase' AND timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY variant_id
            """,
        },
        {
            "name": "session_duration",
            "description": "Average session duration in seconds",
            "unit": "seconds",
            "data_type": "continuous",
            "aggregation_method": "mean",
            "query_template": """
            SELECT
                variant_id,
                AVG(event_value) AS value
            FROM {experiment_id}_events
            WHERE event_type = 'session_end' AND timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY variant_id
            """,
        },
        {
            "name": "click_through_rate",
            "description": "Percentage of users who click on a specific element",
            "unit": "percentage",
            "data_type": "binary",
            "aggregation_method": "mean",
            "query_template": """
            SELECT
                variant_id,
                COUNT(DISTINCT CASE WHEN event_type = 'click' THEN user_id END) / COUNT(DISTINCT user_id) AS value
            FROM {experiment_id}_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY variant_id
            """,
        },
        {
            "name": "bounce_rate",
            "description": "Percentage of users who leave after viewing only one page",
            "unit": "percentage",
            "data_type": "binary",
            "aggregation_method": "mean",
            "query_template": """
            SELECT
                variant_id,
                COUNT(DISTINCT CASE WHEN event_type = 'bounce' THEN user_id END) / COUNT(DISTINCT user_id) AS value
            FROM {experiment_id}_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY variant_id
            """,
        },
        {
            "name": "page_views_per_session",
            "description": "Average number of page views per session",
            "unit": "count",
            "data_type": "continuous",
            "aggregation_method": "mean",
            "query_template": """
            SELECT
                variant_id,
                COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) / COUNT(DISTINCT user_id) AS value
            FROM {experiment_id}_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY variant_id
            """,
        },
        {
            "name": "add_to_cart_rate",
            "description": "Percentage of users who add items to cart",
            "unit": "percentage",
            "data_type": "binary",
            "aggregation_method": "mean",
            "query_template": """
            SELECT
                variant_id,
                COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN user_id END) / COUNT(DISTINCT user_id) AS value
            FROM {experiment_id}_events
            WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY variant_id
            """,
        },
    ]

    for metric_data in metrics:
        metric = (
            db.query(MetricDefinition).filter(MetricDefinition.name == metric_data["name"]).first()
        )
        if not metric:
            metric = MetricDefinition(**metric_data)
            db.add(metric)
            logger.info(f"Added metric definition: {metric_data['name']}")

    db.commit()


def seed_features(db: Session) -> None:
    """Seed feature definitions."""
    features: List[FeatureSeed] = [
        {
            "name": "theme",
            "description": "UI theme for the application",
            "data_type": "string",
            "possible_values": ["light", "dark", "system"],
        },
        {
            "name": "button_color",
            "description": "Color of primary action buttons",
            "data_type": "string",
            "possible_values": ["blue", "green", "red", "purple", "orange"],
        },
        {
            "name": "layout",
            "description": "Page layout configuration",
            "data_type": "string",
            "possible_values": ["default", "compact", "expanded", "sidebar"],
        },
        {
            "name": "show_recommendations",
            "description": "Whether to show personalized recommendations",
            "data_type": "boolean",
            "possible_values": ["true", "false"],
        },
        {
            "name": "pricing_model",
            "description": "Pricing model to display to users",
            "data_type": "string",
            "possible_values": ["monthly", "annual", "lifetime", "freemium"],
        },
        {
            "name": "checkout_flow",
            "description": "Type of checkout flow to show users",
            "data_type": "string",
            "possible_values": ["single_page", "multi_step", "express"],
        },
        {
            "name": "search_algorithm",
            "description": "Algorithm used for search results",
            "data_type": "string",
            "possible_values": ["relevance", "popularity", "hybrid"],
        },
    ]

    for feature_data in features:
        feature = (
            db.query(FeatureDefinition).filter(FeatureDefinition.name == feature_data["name"]).first()
        )
        if not feature:
            feature = FeatureDefinition(**feature_data)
            db.add(feature)
            logger.info(f"Added feature definition: {feature_data['name']}")

    db.commit()


async def seed_ab_test_experiment(db: Session) -> None:
    """Seed an A/B test experiment."""
    experiment = (
        db.query(DBExperiment).filter(DBExperiment.name == "Simple A/B Test").first()
    )

    if experiment:
        logger.info("A/B test experiment already exists, skipping")
        return

    # Create experiment
    experiment = DBExperiment(
        id=str(uuid4()),
        name="Simple A/B Test",
        description="A simple A/B test for demos.",
        type=ExperimentType.AB_TEST,
        hypothesis="Changing the button color to green will increase conversion rate",
        targeting_rules={},
        parameters={},
        status=ExperimentStatus.DRAFT,
        traffic_allocation=100.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        analysis_method=AnalysisMethod.FREQUENTIST,
        confidence_level=0.95,
        correction_method=CorrectionMethod.NONE,
        sequential_testing=True,
        stopping_threshold=0.01,
        metric_configs={
            "conversion_rate": {"min_sample_size": 100, "min_effect_size": 0.05},
            "revenue_per_user": {"min_sample_size": 200, "min_effect_size": 0.1},
        },
        default_metric_config={"min_sample_size": 100, "min_effect_size": 0.01},
    )

    db.add(experiment)
    db.flush()

    # Create variants
    control = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Control",
        type=VariantType.CONTROL,
        config={"button_color": "blue"},
        traffic_percentage=50.0,
    )

    treatment = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Treatment",
        type=VariantType.TREATMENT,
        config={"button_color": "green"},
        traffic_percentage=50.0,
    )

    db.add(control)
    db.add(treatment)

    # Add metrics
    metrics = ["conversion_rate", "revenue_per_user"]
    for metric_name in metrics:
        metric = ExperimentMetric(experiment_id=experiment.id, metric_name=metric_name)
        db.add(metric)

    # Add guardrail metrics
    guardrail = GuardrailMetric(
        experiment_id=experiment.id,
        metric_name="bounce_rate",
        threshold=5.0,
        operator=GuardrailOperator.LESS_THAN,
    )
    db.add(guardrail)

    db.commit()
    logger.info("Created demo experiment")

    # Initialize ClickHouse tables
    data_service = get_data_service(
        metadata_db=db
    )
    try:
        await data_service.initialize_experiment_tables(experiment.id)
        logger.info(f"Initialized ClickHouse tables for experiment {experiment.id}")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse tables: {str(e)}")


async def seed_multivariate_experiment(db: Session) -> None:
    """Seed a multivariate test experiment."""
    experiment = (
        db.query(DBExperiment).filter(DBExperiment.name == "Multivariate Test").first()
    )

    if experiment:
        logger.info("Multivariate experiment already exists, skipping")
        return

    # Create experiment
    experiment = DBExperiment(
        id=str(uuid4()),
        name="Multivariate Test",
        description="A simple multivariate test for demos.",
        type=ExperimentType.MULTIVARIATE,
        hypothesis="Different combinations of layout and theme will affect user engagement",
        targeting_rules={"country": ["US", "CA", "UK"]},
        parameters={},
        status=ExperimentStatus.DRAFT,
        traffic_allocation=80.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        analysis_method=AnalysisMethod.BAYESIAN,
        confidence_level=0.95,
        correction_method=CorrectionMethod.HOLM,
        sequential_testing=True,
        stopping_threshold=0.01,
        metric_configs={
            "session_duration": {"min_sample_size": 500, "min_effect_size": 0.1},
            "page_views_per_session": {"min_sample_size": 500, "min_effect_size": 0.1},
        },
        default_metric_config={"min_sample_size": 500, "min_effect_size": 0.05},
        prior_successes=20,
        prior_trials=100,
    )

    db.add(experiment)
    db.flush()

    # Create variants
    variants = [
        {
            "name": "Control",
            "type": VariantType.CONTROL,
            "config": {"layout": "default", "theme": "light"},
            "traffic_percentage": 25.0,
        },
        {
            "name": "Layout Compact",
            "type": VariantType.TREATMENT,
            "config": {"layout": "compact", "theme": "light"},
            "traffic_percentage": 25.0,
        },
        {
            "name": "Dark Theme",
            "type": VariantType.TREATMENT,
            "config": {"layout": "default", "theme": "dark"},
            "traffic_percentage": 25.0,
        },
        {
            "name": "Compact Dark",
            "type": VariantType.TREATMENT,
            "config": {"layout": "compact", "theme": "dark"},
            "traffic_percentage": 25.0,
        },
    ]

    for variant_data in variants:
        variant = DBVariant(
            id=str(uuid4()),
            experiment_id=experiment.id,
            name=variant_data["name"],
            type=variant_data["type"],
            config=variant_data["config"],
            traffic_percentage=variant_data["traffic_percentage"],
        )
        db.add(variant)

    # Add metrics
    metrics = ["session_duration", "page_views_per_session", "bounce_rate"]
    for metric_name in metrics:
        metric = ExperimentMetric(experiment_id=experiment.id, metric_name=metric_name)
        db.add(metric)

    db.commit()
    logger.info("Created multivariate experiment")

    # Initialize ClickHouse tables
    data_service = get_data_service(
        metadata_db=db
    )
    try:
        await data_service.initialize_experiment_tables(experiment.id)
        logger.info(f"Initialized ClickHouse tables for experiment {experiment.id}")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse tables: {str(e)}")


async def seed_feature_flag_experiment(db: Session) -> None:
    """Seed a feature flag experiment."""
    experiment = (
        db.query(DBExperiment).filter(DBExperiment.name == "Feature Flag Test").first()
    )

    if experiment:
        logger.info("Feature flag experiment already exists, skipping")
        return

    # Create experiment
    experiment = DBExperiment(
        id=str(uuid4()),
        name="Feature Flag Test",
        description="A simple feature flag test for demos.",
        type=ExperimentType.FEATURE_FLAG,
        hypothesis="Showing personalized recommendations will increase engagement and revenue",
        targeting_rules={"user_type": ["registered"]},
        parameters={},
        status=ExperimentStatus.DRAFT,
        traffic_allocation=50.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        analysis_method=AnalysisMethod.FREQUENTIST,
        confidence_level=0.99,
        correction_method=CorrectionMethod.NONE,
        sequential_testing=False,
        metric_configs={
            "revenue_per_user": {"min_sample_size": 1000, "min_effect_size": 0.05},
            "session_duration": {"min_sample_size": 500, "min_effect_size": 0.1},
        },
        default_metric_config={"min_sample_size": 500, "min_effect_size": 0.05},
    )

    db.add(experiment)
    db.flush()

    # Create variants
    control = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Control",
        type=VariantType.CONTROL,
        config={"show_recommendations": "false"},
        traffic_percentage=50.0,
    )

    treatment = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Recommendations On",
        type=VariantType.TREATMENT,
        config={"show_recommendations": "true"},
        traffic_percentage=50.0,
    )

    db.add(control)
    db.add(treatment)

    # Add metrics
    metrics = ["revenue_per_user", "session_duration", "page_views_per_session"]
    for metric_name in metrics:
        metric = ExperimentMetric(experiment_id=experiment.id, metric_name=metric_name)
        db.add(metric)

    # Add guardrail metrics
    guardrail = GuardrailMetric(
        experiment_id=experiment.id,
        metric_name="bounce_rate",
        threshold=10.0,
        operator=GuardrailOperator.LESS_THAN,
    )
    db.add(guardrail)

    db.commit()
    logger.info("Created feature flag experiment")

    # Initialize ClickHouse tables
    data_service = get_data_service(
        metadata_db=db
    )
    try:
        await data_service.initialize_experiment_tables(experiment.id)
        logger.info(f"Initialized ClickHouse tables for experiment {experiment.id}")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse tables: {str(e)}")


async def seed_running_ab_test_experiment(db: Session) -> None:
    """Seed a running A/B test experiment."""
    experiment = (
        db.query(DBExperiment).filter(DBExperiment.name == "Running A/B Test").first()
    )

    if experiment:
        logger.info("Running A/B test experiment already exists, skipping")
        return
    
    # Create experiment
    experiment = DBExperiment(
        id=str(uuid4()),
        name="Running A/B Test",
        description="A running A/B test for demos.",
        type=ExperimentType.AB_TEST,
        status=ExperimentStatus.RUNNING,
        traffic_allocation=100.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        analysis_method=AnalysisMethod.FREQUENTIST,
        confidence_level=0.95,
        correction_method=CorrectionMethod.NONE,
        sequential_testing=True,
        stopping_threshold=0.01,
        metric_configs={
            "conversion_rate": {"min_sample_size": 100, "min_effect_size": 0.05},
            "revenue_per_user": {"min_sample_size": 200, "min_effect_size": 0.1},
        },
        default_metric_config={"min_sample_size": 100, "min_effect_size": 0.01},
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=15),
        ramp_up_period=48,
        auto_stop_conditions={"min_conversions": 1000},
        targeting_rules={"country": ["US", "CA"], "user_type": "registered"},
    )
    db.add(experiment)
    db.flush()
    
    # Create variants
    control = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Control",
        type=VariantType.CONTROL,
        config={"button_color": "blue"},
        traffic_percentage=50.0,
    )
    
    treatment = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Treatment",
        type=VariantType.TREATMENT,
        config={"button_color": "green"},
        traffic_percentage=50.0,
    )
    
    db.add(control)
    db.add(treatment)
    
    # Add metrics
    metrics = ["conversion_rate", "revenue_per_user"]
    for metric_name in metrics:
        metric = ExperimentMetric(experiment_id=experiment.id, metric_name=metric_name)
        db.add(metric)
        
    # Add guardrail metrics
    guardrail = GuardrailMetric(
        experiment_id=experiment.id,
        metric_name="bounce_rate",
        threshold=10.0,
        operator=GuardrailOperator.LESS_THAN,
    )
    db.add(guardrail)
    
    db.commit()
    logger.info("Created running A/B test experiment")

    # Initialize ClickHouse tables
    data_service = get_data_service(
        metadata_db=db
    )
    try:
        await data_service.initialize_experiment_tables(experiment.id)
        logger.info(f"Initialized ClickHouse tables for experiment {experiment.id}")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse tables: {str(e)}")


async def seed_scheduled_ab_test_experiment(db: Session) -> None:
    """Seed a scheduled A/B test experiment."""
    experiment = (
        db.query(DBExperiment).filter(DBExperiment.name == "Scheduled A/B Test").first()
    )
    
    if experiment:
        logger.info("Scheduled A/B test experiment already exists, skipping")
        return
    
    # Create experiment
    experiment = DBExperiment(
        id=str(uuid4()),
        name="Scheduled A/B Test",
        description="A scheduled A/B test for demos.",
        type=ExperimentType.AB_TEST,
        status=ExperimentStatus.SCHEDULED,
        traffic_allocation=100.0,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=15),
        ramp_up_period=48,
        auto_stop_conditions={"min_conversions": 1000},
        targeting_rules={"country": ["US", "CA"], "user_type": "registered"},
        analysis_method=AnalysisMethod.FREQUENTIST,
        confidence_level=0.95,
        correction_method=CorrectionMethod.NONE,
        sequential_testing=True,
        stopping_threshold=0.01,
        metric_configs={
            "conversion_rate": {"min_sample_size": 100, "min_effect_size": 0.05},
            "revenue_per_user": {"min_sample_size": 200, "min_effect_size": 0.1},
        },
        default_metric_config={"min_sample_size": 100, "min_effect_size": 0.01},
    )
    
    db.add(experiment)
    db.flush()
    
    # Create variants
    control = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Control",
        type=VariantType.CONTROL,
        config={"button_color": "blue"},
        traffic_percentage=50.0,
    )
    
    treatment = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Treatment",
        type=VariantType.TREATMENT,
        config={"button_color": "green"},
        traffic_percentage=50.0,
    )
    
    db.add(control)
    db.add(treatment)
    
    # Add metrics
    metrics = ["conversion_rate", "revenue_per_user"]
    for metric_name in metrics:
        metric = ExperimentMetric(experiment_id=experiment.id, metric_name=metric_name)
        db.add(metric)
        
    # Add guardrail metrics
    guardrail = GuardrailMetric(
        experiment_id=experiment.id,
        metric_name="bounce_rate",
        threshold=10.0,
        operator=GuardrailOperator.LESS_THAN,
    )
    db.add(guardrail)
    
    db.commit()
    logger.info("Created scheduled A/B test experiment")
    
    # Initialize ClickHouse tables
    data_service = get_data_service(
        metadata_db=db
    )
    try:
        await data_service.initialize_experiment_tables(experiment.id)
        logger.info(f"Initialized ClickHouse tables for experiment {experiment.id}")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse tables: {str(e)}")

async def seed_completed_ab_test_experiment(db: Session) -> None:
    """Seed a completed A/B test experiment."""
    experiment = (
        db.query(DBExperiment).filter(DBExperiment.name == "Completed A/B Test").first()
    )
    
    if experiment:
        logger.info("Completed A/B test experiment already exists, skipping")
        return
    
    # Create experiment
    experiment = DBExperiment(
        id=str(uuid4()),
        name="Completed A/B Test",
        description="A completed A/B test for demos.",
        type=ExperimentType.AB_TEST,
        status=ExperimentStatus.COMPLETED,
        traffic_allocation=100.0,
        start_time=datetime.utcnow() - timedelta(days=15),
        end_time=datetime.utcnow(),
        ramp_up_period=0,
        auto_stop_conditions={"min_conversions": 1000},
        targeting_rules={"country": ["US", "CA"], "user_type": "registered"},
        analysis_method=AnalysisMethod.FREQUENTIST,
        confidence_level=0.95,
        correction_method=CorrectionMethod.NONE,
        sequential_testing=False,
        stopping_threshold=0.01,
        metric_configs={
            "conversion_rate": {"min_sample_size": 100, "min_effect_size": 0.05},
            "revenue_per_user": {"min_sample_size": 200, "min_effect_size": 0.1},
        },
        default_metric_config={"min_sample_size": 100, "min_effect_size": 0.01},
    )
    
    db.add(experiment)
    db.flush()
    
    # Create variants
    control = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Control",
        type=VariantType.CONTROL,
        config={"button_color": "blue"},
        traffic_percentage=50.0,
    )
    
    treatment = DBVariant(
        id=str(uuid4()),
        experiment_id=experiment.id,
        name="Treatment",
        type=VariantType.TREATMENT,
        config={"button_color": "green"},
        traffic_percentage=50.0,
    )
    
    db.add(control)
    db.add(treatment)
    
    # Add metrics
    metrics = ["conversion_rate", "revenue_per_user"]
    for metric_name in metrics:
        metric = ExperimentMetric(experiment_id=experiment.id, metric_name=metric_name)
        db.add(metric)
        
    # Add guardrail metrics
    guardrail = GuardrailMetric(
        experiment_id=experiment.id,
        metric_name="bounce_rate",
        threshold=10.0,
        operator=GuardrailOperator.LESS_THAN,
    )
    db.add(guardrail)
    
    db.commit()
    logger.info("Created completed A/B test experiment")
    
    # Initialize ClickHouse tables
    data_service = get_data_service(
        metadata_db=db
    )
    try:
        await data_service.initialize_experiment_tables(experiment.id)
        logger.info(f"Initialized ClickHouse tables for experiment {experiment.id}")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse tables: {str(e)}")
        

async def seed_all(db: Session) -> None:
    """Seed all data."""
    seed_metrics(db)
    seed_features(db)
    await seed_ab_test_experiment(db)
    await seed_multivariate_experiment(db)
    await seed_feature_flag_experiment(db)
    await seed_running_ab_test_experiment(db)
    await seed_scheduled_ab_test_experiment(db)
    await seed_completed_ab_test_experiment(db)
    logger.info("Database seeding completed")
