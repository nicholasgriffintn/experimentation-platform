from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import pandas as pd
import pyarrow as pa
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..types import AnalysisMethod, CorrectionMethod, VariantType
from ..utils.logger import logger
from .analysis import CombinedAnalysisService
from .bucketing import BucketingService
from .data import DataService


class VariantConfig(BaseModel):
    id: str
    name: str
    type: VariantType
    config: Dict
    traffic_percentage: float


class MetricConfig(BaseModel):
    name: str
    type: str
    min_sample_size: int
    min_effect_size: float
    query_template: str


class ExperimentSchedule(BaseModel):
    start_time: datetime
    end_time: Optional[datetime]
    ramp_up_period: Optional[int]  # in hours
    auto_stop_conditions: Optional[Dict]


class ExperimentService:
    def __init__(
        self,
        data_service: DataService,
        analysis_service: CombinedAnalysisService,
        bucketing_service: Optional[BucketingService] = None,
        cache_service: Optional[Any] = None,
        db: Optional[Session] = None,
    ):
        self.data_service = data_service
        self.analysis_service = analysis_service
        self.bucketing_service = bucketing_service or BucketingService()
        self.cache_service = cache_service
        self.db = db

    async def _get_user_variant(
        self, experiment_id: str, user_context: Dict
    ) -> Optional[Dict[str, Any]]:
        """Get the variant assigned to a user"""
        user_id = user_context.get("user_id")
        if not user_id:
            return None

        if self.cache_service:
            cached_assignment = await self.cache_service.get_variant_assignment(
                experiment_id, user_id
            )
            if cached_assignment:
                return cached_assignment

        config = await self._get_experiment_config(experiment_id)
        for variant in config.get("variants", []):
            if variant.get("id") == user_id:
                return variant

        return None

    async def _get_experiment_config(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment configuration from cache or database"""
        if not self.db:
            raise ValueError("Database session is required")

        if self.cache_service:
            config = await self.cache_service.get_experiment_config(experiment_id)
            if config:
                return cast(Dict[str, Any], config)

        if not self.data_service:
            raise ValueError("A data service connection is required")

        return await self.data_service.get_experiment_config(experiment_id)

    async def initialize_experiment(self, experiment_id: str, config: Dict) -> bool:
        """Initialize a new experiment with the given configuration

        Args:
            experiment_id: The unique identifier for the experiment
            config: The experiment configuration

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        await self.data_service.set_experiment_config(experiment_id, config)

        if self.cache_service:
            await self.cache_service.set_experiment_config(experiment_id, config)

        return True

    async def resolve_user_variant(
        self, experiment_id: str, user_context: Dict, targeting_type: str = "user_id"
    ) -> Optional[Dict[str, Any]]:
        """Assign a variant to a user based on targeting rules"""
        user_id = user_context.get(targeting_type)
        if not user_id:
            return None

        if self.cache_service:
            cached_assignment = await self.cache_service.get_variant_assignment(
                experiment_id, user_id
            )
            if cached_assignment:
                return cast(Dict[str, Any], cached_assignment)

        config = await self._get_experiment_config(experiment_id)

        if not self._meets_targeting_rules(user_context, config.get("targeting_rules", {})):
            return None

        assignment_key = user_context.get(targeting_type)
        if not assignment_key:
            return None

        variant = self.bucketing_service.assign_variant(
            user_id=user_id,
            experiment_id=experiment_id,
            variants=config["variants"],
            experiment_type=config["type"],
            traffic_allocation=config.get("traffic_allocation", 100.0),
        )

        if variant:
            await self.data_service.record_variant_assignment(
                experiment_id=experiment_id,
                user_id=user_id,
                variant_id=variant["id"],
                context=user_context,
            )

            if self.cache_service:
                await self.cache_service.set_variant_assignment(
                    experiment_id=experiment_id,
                    user_id=user_id,
                    assignment=variant,
                )

        return variant if variant else None

    def _meets_targeting_rules(self, user_context: Dict, targeting_rules: Dict) -> bool:
        """Check if user meets targeting rules"""
        for rule_key, rule_value in targeting_rules.items():
            if rule_key not in user_context:
                return False
            if user_context[rule_key] != rule_value:
                return False
        return True

    async def record_exposure(
        self, experiment_id: str, user_context: Dict, metadata: Optional[Dict] = None
    ) -> None:
        """Record an exposure event for the experiment"""
        await self.data_service.record_event(
            experiment_id=experiment_id,
            event_data={
                "user_id": user_context.get("user_id"),
                "event_type": "exposure",
                "metadata": metadata or {},
            },
        )

    async def track_user_metric(
        self,
        experiment_id: str,
        metric_name: str,
        value: float,
        user_context: Dict,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Record a metric measurement for the experiment"""
        variant = await self._get_user_variant(experiment_id, user_context)
        if not variant:
            return

        await self.data_service.record_metric(
            experiment_id=experiment_id,
            metric_data={
                "metric_name": metric_name,
                "metric_value": value,
                "variant_id": variant["id"],
                "user_id": user_context.get("user_id"),
                "metadata": metadata or {},
            },
        )

    async def analyze_results(
        self, experiment_id: str, metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze current experiment results with multiple testing correction"""
        logger.info(f"Analyzing results for experiment {experiment_id}")
        config = await self._get_experiment_config(experiment_id)

        if metrics:
            metrics_to_analyze = metrics
        else:
            metrics_to_analyze = []
            config_metrics = config.get("metrics", [])
            for metric in config_metrics:
                if isinstance(metric, dict):
                    metrics_to_analyze.append(metric.get("metric_name") or metric.get("name"))
                elif isinstance(metric, str):
                    metrics_to_analyze.append(metric)
                else:
                    try:
                        metrics_to_analyze.append(metric.metric_name)
                    except AttributeError:
                        logger.warning(f"Could not extract metric name from {metric}")

        if not metrics_to_analyze:
            logger.warning(f"No metrics to analyze for experiment {experiment_id}")
            return {
                "experiment_id": experiment_id,
                "status": config.get("status", "running"),
                "start_time": config.get("start_time", datetime.utcnow()),
                "end_time": config.get("end_time"),
                "total_users": 0,
                "metrics": {},
                "correction_method": None,
            }

        metrics_results = {}
        total_users = 0
        all_p_values = []
        variant_p_values = {}

        for metric_name in metrics_to_analyze:
            if self.cache_service:
                cached_stats = await self.cache_service.get_metric_stats(experiment_id, metric_name)
                if cached_stats:
                    metrics_results[metric_name] = cached_stats
                    continue

            metric_data = await self._get_metric_data(experiment_id, metric_name)
            metrics_results[metric_name] = {}

            if not metric_data:
                continue

            control_data = metric_data.get("control", [])
            total_users = max(total_users, len(control_data))

            for variant_id, variant_data in metric_data.items():
                if variant_id == "control":
                    continue

                total_users = max(total_users, len(variant_data))

                if not variant_data:
                    continue

                analysis_config = config.get("analysis_config", {})
                method = analysis_config.get("method", AnalysisMethod.FREQUENTIST)
                sequential = analysis_config.get("sequential_testing", False)
                stopping_threshold = analysis_config.get("stopping_threshold", 0.01)

                # Find metric type from config
                metric_type = "continuous"  # default
                for m in config.get("metrics", []):
                    if isinstance(m, dict) and (
                        m.get("metric_name") == metric_name or m.get("name") == metric_name
                    ):
                        metric_type = m.get("type", "continuous")
                        break

                try:
                    analysis_result = await self.analysis_service.analyze_experiment(
                        control_data=control_data,
                        variant_data=variant_data,
                        metric_name=metric_name,
                        metric_type=metric_type,
                        alpha=config.get("analysis_config", {}).get("alpha", 0.05),
                        correction_method=config.get("analysis_config", {}).get(
                            "correction_method"
                        ),
                        method=method,
                        sequential=sequential,
                        stopping_threshold=stopping_threshold,
                    )

                    all_p_values.append(analysis_result.frequentist_results.p_value)
                    variant_p_values[(metric_name, variant_id)] = len(all_p_values) - 1
                    metrics_results[metric_name][variant_id] = {
                        "sample_size": len(variant_data),
                        "mean": float(analysis_result.frequentist_results.variant_mean),
                        "variance": float(
                            (
                                analysis_result.frequentist_results.confidence_interval[1]
                                - analysis_result.frequentist_results.confidence_interval[0]
                            )
                            / 3.92
                        ),
                        "confidence_level": 0.95,
                        "p_value": float(analysis_result.frequentist_results.p_value),
                    }

                    if self.cache_service:
                        await self.cache_service.set_metric_stats(
                            experiment_id=experiment_id,
                            metric_name=metric_name,
                            stats=metrics_results[metric_name],
                        )
                except Exception as e:
                    logger.error(
                        f"Error analyzing metric {metric_name} for variant {variant_id}: {str(e)}"
                    )
                    metrics_results[metric_name][variant_id] = {
                        "sample_size": len(variant_data),
                        "mean": float(sum(variant_data) / len(variant_data)) if variant_data else 0,
                        "error": str(e),
                    }

        correction_method = None
        if len(all_p_values) > 1:
            correction_method = config.get("analysis_config", {}).get(
                "correction_method", CorrectionMethod.FDR_BH
            )
            try:
                corrected_p_values = self.analysis_service.correction_service.apply_correction(
                    all_p_values, method=correction_method
                )

                for (metric_name, variant_id), p_value_idx in variant_p_values.items():
                    corrected_p_value = corrected_p_values[p_value_idx]
                    metrics_results[metric_name][variant_id]["p_value"] = corrected_p_value
                    metrics_results[metric_name][variant_id]["is_significant"] = (
                        corrected_p_value < config.get("analysis_config", {}).get("alpha", 0.05)
                    )
            except Exception as e:
                logger.error(f"Error applying correction to p-values: {str(e)}")

        results = {
            "experiment_id": experiment_id,
            "status": config.get("status", "running"),
            "start_time": config.get("start_time", datetime.utcnow()),
            "end_time": config.get("end_time"),
            "total_users": total_users,
            "metrics": metrics_results,
            "correction_method": correction_method if len(all_p_values) > 1 else None,
        }

        try:
            await self.data_service.record_results(
                experiment_id=experiment_id, results_data=results
            )
        except Exception as e:
            logger.warning(f"Failed to record results for experiment {experiment_id}: {str(e)}")

        return results

    async def _get_metric_data(
        self, experiment_id: str, metric_name: str
    ) -> Dict[str, List[float]]:
        """Get metric data grouped by variant"""
        metric_history = await self.data_service.get_metric_history(
            experiment_id=experiment_id, metric_name=metric_name
        )

        if not metric_history:
            return {}

        try:
            if isinstance(metric_history, pa.ChunkedArray):
                table = pa.Table.from_arrays([metric_history], names=["data"])
                df = table.to_pandas()
            elif isinstance(metric_history, pa.Table):
                df = metric_history.to_pandas()
            else:
                df = pd.DataFrame(metric_history)

            if "variant_id" not in df.columns or "metric_value" not in df.columns:
                return {}

            grouped_data = {}
            for variant_id, group in df.groupby("variant_id"):
                grouped_data[variant_id] = group["metric_value"].tolist()
            return grouped_data

        except Exception:
            return {}

    async def pause_experiment(self, experiment_id: str, reason: Optional[str] = None) -> None:
        """Pause an experiment"""
        await self.data_service.record_event(
            experiment_id=experiment_id, event_data={"event_type": "pause", "reason": reason}
        )

    async def resume_experiment(self, experiment_id: str) -> None:
        """Resume a paused experiment"""
        await self.data_service.record_event(
            experiment_id=experiment_id, event_data={"event_type": "resume"}
        )

    async def stop_experiment(self, experiment_id: str, reason: Optional[str] = None) -> None:
        """Stop an experiment"""
        await self.data_service.record_event(
            experiment_id=experiment_id, event_data={"event_type": "stop", "reason": reason}
        )

        config = await self._get_experiment_config(experiment_id)
        if config:
            config["status"] = "stopped"
            config["stopped_reason"] = reason

            await self.data_service.set_experiment_config(experiment_id, config)

            if self.cache_service:
                await self.cache_service.set_experiment_config(experiment_id, config)

    async def update_schedule(self, experiment_id: str, schedule: Dict) -> None:
        """Update experiment schedule"""
        await self.data_service.record_event(
            experiment_id=experiment_id,
            event_data={"event_type": "schedule_update", "schedule": schedule},
        )

        if self.cache_service:
            config = await self._get_experiment_config(experiment_id)
            if config:
                config["schedule"] = schedule

                await self.data_service.set_experiment_config(experiment_id, config)

                if self.cache_service:
                    await self.cache_service.set_experiment_config(experiment_id, config)

    async def get_results(
        self, experiment_id: str, metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get the most recent results for an experiment

        This method first tries to retrieve stored results from the database.
        If no stored results exist, it performs a new analysis.

        Args:
            experiment_id: ID of the experiment
            metrics: Optional list of specific metrics to analyze

        Returns:
            Dictionary with experiment results
        """
        logger.info(f"Getting results for experiment {experiment_id}")

        stored_results = await self.data_service.get_stored_results(experiment_id)

        if stored_results:
            logger.info(f"Using stored results for experiment {experiment_id}")
            if metrics and stored_results.get("metrics"):
                filtered_metrics = {}
                for metric_name in metrics:
                    if metric_name in stored_results["metrics"]:
                        filtered_metrics[metric_name] = stored_results["metrics"][metric_name]
                stored_results["metrics"] = filtered_metrics
            return stored_results

        logger.info(
            f"No stored results found for experiment {experiment_id}, performing new analysis"
        )
        return await self.analyze_results(experiment_id=experiment_id, metrics=metrics)
