from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session

from .db.session import get_db
from .services.experiments import ExperimentService
from .services.analysis import StatisticalAnalysisService
from .services.data import IcebergDataService
from .services.scheduler import ExperimentScheduler
from .config.app import settings
from .config.iceberg import IcebergConfig, create_catalog

@lru_cache
def get_iceberg_service() -> IcebergDataService:
    """Get cached IcebergDataService instance."""
    config = IcebergConfig(
        warehouse_location=settings.warehouse_location,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        aws_region=settings.aws_region
    )
    catalog = create_catalog(config)
    return IcebergDataService(catalog=catalog)

@lru_cache
def get_stats_service() -> StatisticalAnalysisService:
    """Get cached StatisticalAnalysisService instance."""
    return StatisticalAnalysisService(
        min_sample_size=100,
        confidence_level=0.95
    )

def get_experiment_service(
    db: Session = Depends(get_db),
    iceberg_service: IcebergDataService = Depends(get_iceberg_service),
    stats_service: StatisticalAnalysisService = Depends(get_stats_service)
) -> ExperimentService:
    """Get ExperimentService instance."""
    return ExperimentService(
        data_service=iceberg_service,
        stats_service=stats_service
    )

def get_scheduler(
    experiment_service: ExperimentService = Depends(get_experiment_service),
    db: Session = Depends(get_db)
) -> ExperimentScheduler:
    """Get ExperimentScheduler instance with active database session."""
    return ExperimentScheduler(
        experiment_service=experiment_service,
        db=db,
        check_interval=60
    )