from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from .config.app import settings
from .routers import experiments, metrics, features
from .dependencies import get_db, get_experiment_service
from .db.base import Base
from .db.session import engine
from .services.scheduler import ExperimentScheduler

app = FastAPI(
    title=settings.api_name,
    description=settings.api_description,
    version=settings.api_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(features.router, prefix="/api/v1/features", tags=["features"])

scheduler = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    if settings.scheduler_enabled:
        print("Starting scheduler")
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
        print("Scheduler is disabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    if scheduler:
        print("Stopping scheduler")
        await scheduler.stop()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scheduler": "running" if scheduler and scheduler.running else "stopped"
    }