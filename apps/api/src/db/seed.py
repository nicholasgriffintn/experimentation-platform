from datetime import datetime, timedelta
from typing import List, TypedDict
from uuid import uuid4

from pyiceberg.catalog import load_catalog
from sqlalchemy.orm import Session

from ..config.app import settings
from ..models.analysis_model import AnalysisMethod, CorrectionMethod
from ..models.experiments_model import ExperimentStatus, ExperimentType
from ..models.variants_model import VariantConfig, VariantType
from ..models.guardrails_model import GuardrailOperator
from ..services.data import IcebergDataService
from ..utils.logger import logger
from .base import Experiment as DBExperiment
from .base import ExperimentMetric, FeatureDefinition, GuardrailMetric, MetricDefinition
from .base import Variant as DBVariant


def get_data_service() -> IcebergDataService:
    """Get initialized data service instance."""
    catalog = load_catalog(settings.iceberg_catalog_name, **settings.iceberg_catalog_config)

    try:
        namespaces = catalog.list_namespaces()
        if (settings.iceberg_namespace,) not in namespaces:
            catalog.create_namespace(
                settings.iceberg_namespace,
                {
                    "location": f"{settings.iceberg_warehouse}{settings.iceberg_namespace}",
                    "owner": "experimentation-platform",
                    "description": "Namespace for experiment data",
                },
            )
            logger.info(f"Created {settings.iceberg_namespace} namespace")
        else:
            pass
    except Exception as e:
        if "NamespaceAlreadyExistsException" in str(e):
            pass
        else:
            logger.warning(f"Failed to handle namespace: {str(e)}")

    return IcebergDataService(catalog)


def seed_default_feature_values(db: Session) -> None:
    """Seed default feature values for boolean feature flags."""

    boolean_feature = FeatureDefinition(
        name="enabled",
        description="Standard boolean feature flag for enabling/disabling features",
        data_type="boolean",
        possible_values=[True, False],
    )

    existing = (
        db.query(FeatureDefinition).filter(FeatureDefinition.name == boolean_feature.name).first()
    )
    if not existing:
        db.add(boolean_feature)
        db.commit()


def seed_test_metrics(db: Session) -> None:
    """Seed test metrics for experiments."""
    test_metrics = [
        MetricDefinition(
            name="conversion_rate",
            description="Percentage of users who complete a purchase",
            unit="%",
            data_type="binary",
            aggregation_method="mean",
            query_template="SELECT user_id, CASE WHEN purchase_completed THEN 1 ELSE 0 END as value FROM purchases",
        ),
        MetricDefinition(
            name="average_order_value",
            description="Average amount spent per order",
            unit="£",
            data_type="continuous",
            aggregation_method="mean",
            query_template="SELECT user_id, order_total as value FROM orders",
        ),
        MetricDefinition(
            name="page_views",
            description="Number of page views per user",
            unit="count",
            data_type="count",
            aggregation_method="sum",
            query_template="SELECT user_id, COUNT(*) as value FROM page_views GROUP BY user_id",
        ),
        MetricDefinition(
            name="bounce_rate",
            description="Percentage of users who leave after viewing only one page",
            unit="%",
            data_type="ratio",
            aggregation_method="ratio",
            query_template="SELECT user_id, (sessions_with_one_page * 1.0 / total_sessions) as value FROM user_sessions",
        ),
    ]

    for metric in test_metrics:
        existing = db.query(MetricDefinition).filter(MetricDefinition.name == metric.name).first()
        if not existing:
            db.add(metric)

    db.commit()


class GuardrailConfig(TypedDict):
    metric: str
    threshold: float
    operator: GuardrailOperator


class ExperimentConfig(TypedDict):
    exp: DBExperiment
    variants: List[DBVariant]
    metrics: List[str]
    guardrails: List[GuardrailConfig]


async def seed_test_experiments(db: Session) -> None:
    """Seed test experiments covering various use cases."""
    now = datetime.utcnow()
    data_service = get_data_service()

    experiments: List[ExperimentConfig] = [
        # 1. Simple A/B Test (Draft)
        {
            "exp": DBExperiment(
                id=str(uuid4()),
                name="Simple Button Color Test",
                description="Testing impact of button color on conversion rate",
                type=ExperimentType.AB_TEST,
                hypothesis="Changing the button color to blue will increase conversion rate",
                status=ExperimentStatus.DRAFT,
                traffic_allocation=100.0,
                analysis_method=AnalysisMethod.FREQUENTIST,
                confidence_level=0.95,
                correction_method=CorrectionMethod.NONE,
            ),
            "variants": [
                VariantConfig(
                    id=str(uuid4()),
                    name="control",
                    type=VariantType.CONTROL,
                    config={"color": "green"},
                    traffic_percentage=50,
                ),
                VariantConfig(
                    id=str(uuid4()),
                    name="treatment",
                    type=VariantType.TREATMENT,
                    config={"color": "blue"},
                    traffic_percentage=50,
                ),
            ],
            "metrics": ["conversion_rate"],
            "guardrails": [],
        },
        # 2. Multivariate Test (Running)
        {
            "exp": DBExperiment(
                id=str(uuid4()),
                name="Homepage Layout Optimization",
                description="Testing different homepage layouts and hero images",
                type=ExperimentType.MULTIVARIATE,
                hypothesis="New layout with lifestyle imagery will increase engagement and sales",
                status=ExperimentStatus.RUNNING,
                traffic_allocation=80.0,
                started_at=now - timedelta(days=5),
                start_time=now - timedelta(days=5),
                end_time=now + timedelta(days=25),
                ramp_up_period=24,
                analysis_method=AnalysisMethod.BAYESIAN,
                confidence_level=0.95,
                correction_method=CorrectionMethod.FDR_BH,
                prior_successes=30,
                prior_trials=100,
                num_samples=10000,
            ),
            "variants": [
                VariantConfig(
                    id=str(uuid4()),
                    name="control",
                    type=VariantType.CONTROL,
                    config={"layout": "classic", "hero": "product"},
                    traffic_percentage=25,
                ),
                VariantConfig(
                    id=str(uuid4()),
                    name="layout_v1",
                    type=VariantType.TREATMENT,
                    config={"layout": "modern", "hero": "product"},
                    traffic_percentage=25,
                ),
                VariantConfig(
                    id=str(uuid4()),
                    name="layout_v2",
                    type=VariantType.TREATMENT,
                    config={"layout": "classic", "hero": "lifestyle"},
                    traffic_percentage=25,
                ),
                VariantConfig(
                    id=str(uuid4()),
                    name="layout_v3",
                    type=VariantType.TREATMENT,
                    config={"layout": "modern", "hero": "lifestyle"},
                    traffic_percentage=25,
                ),
            ],
            "metrics": ["conversion_rate", "average_order_value", "page_views"],
            "guardrails": [],
        },
        # 3. Feature Flag Test (Scheduled)
        {
            "exp": DBExperiment(
                id=str(uuid4()),
                name="New Checkout Flow",
                description="Testing new streamlined checkout process",
                type=ExperimentType.FEATURE_FLAG,
                hypothesis="New checkout flow will reduce cart abandonment",
                status=ExperimentStatus.SCHEDULED,
                traffic_allocation=20.0,
                start_time=now + timedelta(days=1),
                end_time=now + timedelta(days=15),
                ramp_up_period=48,
                auto_stop_conditions={"min_conversions": 1000},
                targeting_rules={"country": ["US", "CA"], "user_type": "registered"},
                analysis_method=AnalysisMethod.FREQUENTIST,
                confidence_level=0.95,
                correction_method=CorrectionMethod.NONE,
            ),
            "variants": [
                VariantConfig(
                    id=str(uuid4()),
                    name="control",
                    type=VariantType.CONTROL,
                    config={"checkout_version": "current"},
                    traffic_percentage=50,
                ),
                VariantConfig(
                    id=str(uuid4()),
                    name="new_flow",
                    type=VariantType.FEATURE_FLAG,
                    config={"checkout_version": "new"},
                    traffic_percentage=50,
                ),
            ],
            "metrics": ["conversion_rate", "average_order_value"],
            "guardrails": [{"metric": "conversion_rate", "threshold": 0.9, "operator": GuardrailOperator.GREATER_THAN}],
        },
        # 4. Completed A/B Test
        {
            "exp": DBExperiment(
                id=str(uuid4()),
                name="Price Sensitivity Test",
                description="Testing impact of 10% price reduction",
                type=ExperimentType.AB_TEST,
                hypothesis="10% price reduction will increase overall revenue through volume",
                status=ExperimentStatus.COMPLETED,
                traffic_allocation=100.0,
                started_at=now - timedelta(days=30),
                ended_at=now - timedelta(days=2),
                start_time=now - timedelta(days=30),
                end_time=now - timedelta(days=2),
                analysis_method=AnalysisMethod.FREQUENTIST,
                confidence_level=0.99,
                correction_method=CorrectionMethod.HOLM,
            ),
            "variants": [
                VariantConfig(
                    id=str(uuid4()),
                    name="control",
                    type=VariantType.CONTROL,
                    config={"discount": 0},
                    traffic_percentage=50,
                ),
                VariantConfig(
                    id=str(uuid4()),
                    name="discount",
                    type=VariantType.TREATMENT,
                    config={"discount": 10},
                    traffic_percentage=50,
                ),
            ],
            "metrics": ["conversion_rate", "average_order_value"],
            "guardrails": [],
        },
        # 5. Paused A/B Test
        {
            "exp": DBExperiment(
                id=str(uuid4()),
                name="New User Onboarding Flow",
                description="Testing simplified onboarding process",
                type=ExperimentType.AB_TEST,
                hypothesis="Simplified onboarding will increase completion rate",
                status=ExperimentStatus.PAUSED,
                traffic_allocation=50.0,
                started_at=now - timedelta(days=3),
                start_time=now - timedelta(days=3),
                end_time=now + timedelta(days=27),
                targeting_rules={"user_type": "new"},
                analysis_method=AnalysisMethod.FREQUENTIST,
                confidence_level=0.95,
                correction_method=CorrectionMethod.NONE,
            ),
            "variants": [
                VariantConfig(
                    id=str(uuid4()),
                    name="control",
                    type=VariantType.CONTROL,
                    config={"onboarding_steps": 5},
                    traffic_percentage=50,
                ),
                VariantConfig(
                    id=str(uuid4()),
                    name="simplified",
                    type=VariantType.TREATMENT,
                    config={"onboarding_steps": 3},
                    traffic_percentage=50,
                ),
            ],
            "metrics": ["conversion_rate", "page_views"],
            "guardrails": [],
        },
    ]

    for exp_config in experiments:
        existing = (
            db.query(DBExperiment).filter(DBExperiment.name == exp_config["exp"].name).first()
        )
        if not existing:
            exp: DBExperiment = exp_config["exp"]
            db.add(exp)
            db.flush()

            try:
                logger.info(f"Initializing Iceberg tables for experiment {exp.id}")
                tables_initialized = await data_service.initialize_experiment_tables(exp.id)
                
                if not tables_initialized:
                    logger.error(f"Failed to initialize tables for experiment {exp.id}, skipping")
                    db.rollback()
                    continue

                for variant_config in exp_config["variants"]:
                    db_variant = DBVariant(
                        id=variant_config.id,
                        experiment_id=exp.id,
                        name=variant_config.name,
                        type=variant_config.type.value,
                        config=variant_config.config,
                        traffic_percentage=variant_config.traffic_percentage,
                    )
                    db.add(db_variant)

                for metric_name in exp_config["metrics"]:
                    metric = ExperimentMetric(experiment_id=exp.id, metric_name=metric_name)
                    db.add(metric)

                for guardrail in exp_config["guardrails"]:
                    guardrail_metric = GuardrailMetric(
                        experiment_id=exp.id,
                        metric_name=guardrail["metric"],
                        threshold=guardrail["threshold"],
                        operator=str(guardrail["operator"].value),
                    )
                    db.add(guardrail_metric)

                db.commit()
                logger.info(f"Successfully seeded experiment {exp.id}")

            except Exception as e:
                db.rollback()
                logger.error(f"Failed to seed experiment {exp.name}: {str(e)}")
                continue


async def seed_all(db: Session) -> None:
    """Run all seed functions."""
    seed_default_feature_values(db)
    seed_test_metrics(db)
    await seed_test_experiments(db)
