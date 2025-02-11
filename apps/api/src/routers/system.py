from fastapi import APIRouter

from ..services.system_metrics import system_metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    Get all system metrics.

    Returns:
        dict: The metrics for all services
    """
    return system_metrics.get_metrics()


@router.get("/metrics/{service}")
async def get_service_metrics(service: str):
    """
    Get metrics for a specific service.

    Args:
        service (str): The name of the service to get metrics for

    Returns:
        dict: The metrics for the specified service
    """
    return system_metrics.get_metrics(service)
