import asyncio
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.app import settings
from .db.base import Base
from .db.seed import seed_all
from .db.session import engine
from .dependencies import get_db, get_experiment_service
from .middleware.error_handler import error_handler
from .routers import experiments, features, metrics
from .services.scheduler import ExperimentScheduler
from .utils.logger import LogConfig, logger

logging.config.dictConfig(LogConfig().dict())

description = """
This API provides a comprehensive suite of endpoints for managing and analyzing experiments and feature flags.
"""

tags_metadata = [
    {
        "name": "experiments",
        "description": "Manage A/B tests and experiments. Includes creation, monitoring, and analysis endpoints.",
    },
    {
        "name": "metrics",
        "description": "Define and manage metrics that can be tracked in experiments.",
    },
    {
        "name": "features",
        "description": "Manage feature definitions and configurations for experiments.",
    },
]

app = FastAPI(
    title=settings.api_name,
    description=description,
    version=settings.api_version,
    openapi_tags=tags_metadata,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "Nicholas Griffin",
        "url": "https://nicholasgriffin.dev",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(error_handler)

Base.metadata.create_all(bind=engine)

app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(features.router, prefix="/api/v1/features", tags=["features"])

scheduler = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    if settings.scheduler_enabled:
        logger.info("Starting scheduler")
        global scheduler
        db = next(get_db())
        experiment_service = get_experiment_service(db)
        scheduler = ExperimentScheduler(
            experiment_service=experiment_service,
            db=db,
            check_interval=60
        )
        asyncio.create_task(scheduler.start())
    else:
        logger.info("Scheduler is disabled")

    db = next(get_db())
    await seed_all(db)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    if scheduler:
        logger.info("Stopping scheduler")
        await scheduler.stop()

@app.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: A dictionary containing the API status and scheduler state
        
    Example Response:
        {
            "status": "healthy",
            "scheduler": "running"
        }
    """
    return {
        "status": "healthy",
        "scheduler": "running" if scheduler and scheduler.running else "stopped"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
