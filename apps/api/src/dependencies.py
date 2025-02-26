from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from .config.app import settings
from .db.session import get_db
from .services.analysis import (
    BayesianAnalysisService,
    CombinedAnalysisService,
    MultipleTestingCorrection,
    StatisticalAnalysisService,
)
from .services.cache import CacheService, RedisCache
from .services.clickhouse_data import ClickHouseDataService
from .services.experiments import ExperimentService
from .services.scheduler import ExperimentScheduler


@lru_cache
def get_clickhouse_service() -> ClickHouseDataService:
    """Get cached ClickHouseDataService instance."""
    return ClickHouseDataService(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        user=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


@lru_cache
def get_frequentist_service() -> StatisticalAnalysisService:
    """Get cached StatisticalAnalysisService instance."""
    return StatisticalAnalysisService()


@lru_cache
def get_bayesian_service() -> BayesianAnalysisService:
    """Get cached BayesianAnalysisService instance."""
    return BayesianAnalysisService()


@lru_cache
def get_correction_service() -> MultipleTestingCorrection:
    """Get cached MultipleTestingCorrection instance."""
    return MultipleTestingCorrection()


@lru_cache
def get_analysis_service(
    frequentist_service: StatisticalAnalysisService = Depends(get_frequentist_service),
    bayesian_service: BayesianAnalysisService = Depends(get_bayesian_service),
    correction_service: MultipleTestingCorrection = Depends(get_correction_service),
) -> CombinedAnalysisService:
    """Get cached CombinedAnalysisService instance."""
    return CombinedAnalysisService(
        frequentist_service=frequentist_service,
        bayesian_service=bayesian_service,
        correction_service=correction_service,
    )


@lru_cache
def get_cache_service() -> CacheService:
    """Get cached CacheService instance."""
    redis_cache = RedisCache(settings.redis_url)
    return CacheService(redis_cache)


@lru_cache
def get_experiment_service(
    db: Session = Depends(get_db),
    data_service: ClickHouseDataService = Depends(get_clickhouse_service),
    analysis_service: CombinedAnalysisService = Depends(get_analysis_service),
    cache_service: CacheService = Depends(get_cache_service),
) -> ExperimentService:
    """Get ExperimentService instance with all dependencies."""
    return ExperimentService(
        data_service=data_service,
        analysis_service=analysis_service,
        cache_service=cache_service,
        db=db,
    )

def get_scheduler(
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db),
) -> ExperimentScheduler:
    """Get ExperimentScheduler instance with active database session."""
    return ExperimentScheduler(experiment_service=experiment_service, db=db, check_interval=60)

