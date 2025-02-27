from typing import Any, Dict


class SystemMetricsService:
    """
    Centralized service for collecting and managing system metrics.
    """

    def __init__(self) -> None:
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def increment(self, service: str, metric: str, value: int = 1) -> None:
        """Increment a counter metric"""
        if service not in self._metrics:
            self._metrics[service] = {}
        if metric not in self._metrics[service]:
            self._metrics[service][metric] = 0
        self._metrics[service][metric] += value

    def record_time(self, service: str, metric: str, duration: float) -> None:
        """Record a timing metric"""
        if service not in self._metrics:
            self._metrics[service] = {}
        self._metrics[service][metric] = duration

    def get_metrics(self, service: str = None) -> Dict[str, Any]:
        """Get all metrics or metrics for a specific service"""
        if service:
            return self._metrics.get(service, {})
        return self._metrics


system_metrics = SystemMetricsService()

__all__ = ["system_metrics"]
