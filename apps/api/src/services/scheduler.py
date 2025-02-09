import asyncio
from datetime import datetime
from typing import Dict, Optional, Set, List

from sqlalchemy.orm import Session

from ..db.base import Experiment
from ..models.analysis_model import AnalysisMethod
from ..models.experiments_model import ExperimentStatus
from ..models.guardrails_model import GuardrailMetric, GuardrailOperator
from ..utils.logger import logger
from .experiments import ExperimentService


class ExperimentScheduler:
    def __init__(
        self, experiment_service: ExperimentService, db: Session, check_interval: int = 60
    ) -> None:
        self.experiment_service = experiment_service
        self.db = db
        self.check_interval = check_interval
        self.running = False
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        """Start the scheduler"""
        self.running = True
        while self.running:
            await self.check_experiments()
            await asyncio.sleep(self.check_interval)

    async def stop(self) -> None:
        """Stop the scheduler"""
        self.running = False
        for task in self.scheduled_tasks.values():
            task.cancel()

    async def check_experiments(self) -> None:
        """If scheduled, start the experiment, stop if it should end. Check guardrails for running experiments."""
        now = datetime.utcnow()

        experiments = (
            self.db.query(Experiment)
            .filter(Experiment.status.in_([ExperimentStatus.DRAFT, ExperimentStatus.RUNNING]))
            .all()
        )

        for experiment in experiments:
            if (
                experiment.status == ExperimentStatus.DRAFT
                and experiment.start_time
                and experiment.start_time <= now
            ):
                await self.start_experiment(experiment)

            elif experiment.status == ExperimentStatus.RUNNING:
                if experiment.end_time and experiment.end_time <= now:
                    await self.stop_experiment(experiment)
                    continue

                await self.check_guardrails(experiment)

                if experiment.auto_stop_conditions:
                    await self.check_auto_stop_conditions(experiment)

    async def start_experiment(self, experiment: Experiment) -> None:
        """Start an experiment and schedule automated analysis if needed"""
        try:
            if experiment.ramp_up_period:
                await self._apply_ramp_up_traffic(experiment)
            else:
                setattr(experiment, "status", ExperimentStatus.RUNNING)

            setattr(experiment, "started_at", datetime.utcnow())
            self.db.commit()

            if experiment.parameters.get("auto_analyze_interval"):
                self.schedule_automated_analysis(experiment)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error starting experiment {experiment.id}: {str(e)}")

    async def _apply_ramp_up_traffic(self, experiment: Experiment) -> None:
        """Apply initial traffic allocation for ramp-up"""
        try:
            initial_traffic_percentage = 10.0
            setattr(experiment, "traffic_allocation", initial_traffic_percentage)
            setattr(experiment, "status", ExperimentStatus.RUNNING)
            self.db.commit()

            total_hours = experiment.ramp_up_period or 24
            steps = 5
            hours_per_step = total_hours / steps

            for step in range(1, steps + 1):
                task_key = f"{str(experiment.id)}_rampup_{step}"
                self.scheduled_tasks[task_key] = asyncio.create_task(
                    self._schedule_traffic_increase(
                        experiment_id=str(experiment.id),
                        delay_hours=float(hours_per_step * step),
                        target_percentage=initial_traffic_percentage
                        + ((100 - initial_traffic_percentage) * step / steps),
                    )
                )

        except Exception as e:
            print(f"Error applying ramp-up for experiment {experiment.id}: {str(e)}")
            logger.error(f"Error applying ramp-up for experiment {experiment.id}: {str(e)}")
            raise

    async def _schedule_traffic_increase(
        self, experiment_id: str, delay_hours: float, target_percentage: float
    ) -> None:
        """Schedule a traffic increase after a delay"""
        await asyncio.sleep(delay_hours * 3600)

        experiment = (
            self.db.query(Experiment)
            .filter(Experiment.id == experiment_id, Experiment.status == ExperimentStatus.RUNNING)
            .first()
        )

        if experiment:
            try:
                setattr(experiment, "traffic_allocation", target_percentage)
                self.db.commit()

                await self.experiment_service.data_service.record_event(
                    experiment_id=experiment_id,
                    event_data={
                        "event_type": "traffic_allocation_update",
                        "traffic_allocation": target_percentage,
                    },
                )
            except Exception as e:
                logger.error(f"Error increasing traffic for experiment {experiment_id}: {str(e)}")

    async def _get_experiment_sample_size(self, experiment: Experiment) -> int:
        """
        Get the current sample size of the experiment.
        Returns the size of the smallest variant group (control or treatment)
        to ensure we have sufficient data across all variants.
        """
        try:
            exposure_data = await self.experiment_service.data_service.get_exposure_data(
                str(experiment.id)
            )
            if not exposure_data:
                return 0

            variant_sizes: Dict[str, Set[str]] = {}
            for record in exposure_data:
                variant_id = record.get("variant_id")
                user_id = record.get("user_id")

                if not variant_id or not user_id:
                    continue

                if variant_id not in variant_sizes:
                    variant_sizes[variant_id] = set()
                variant_sizes[variant_id].add(user_id)

            if not variant_sizes:
                return 0

            return min(len(users) for users in variant_sizes.values())

        except Exception as e:
            logger.error(f"Error getting sample size for experiment {experiment.id}: {str(e)}")
            return 0

    def is_guardrail_violated(
        self, metric_data: Dict[str, List[float]], guardrail: GuardrailMetric
    ) -> bool:
        """Check if a guardrail metric is violated"""
        for variant_id, values in metric_data.items():
            if not values:
                continue

            metric_value = sum(values) / len(values)

            if guardrail.operator == "gt" and metric_value > guardrail.threshold:
                return True
            elif guardrail.operator == "lt" and metric_value < guardrail.threshold:
                return True
            elif guardrail.operator == "gte" and metric_value >= guardrail.threshold:
                return True
            elif guardrail.operator == "lte" and metric_value <= guardrail.threshold:
                return True

        return False

    async def check_auto_stop_conditions(self, experiment: Experiment) -> None:
        """Check if any auto-stop conditions are met"""
        conditions = experiment.auto_stop_conditions
        if not conditions:
            return

        try:
            if "min_sample_size" in conditions:
                min_sample_size = int(conditions["min_sample_size"])
                sample_size = await self._get_experiment_sample_size(experiment)
                if sample_size and sample_size >= min_sample_size:
                    await self.stop_experiment(experiment, reason="Reached target sample size")
                    return

            results = await self.experiment_service.analyze_results(str(experiment.id))

            if getattr(experiment, "analysis_config", {}).get("sequential_testing"):
                stopping_threshold = float(
                    getattr(experiment, "analysis_config", {}).get("stopping_threshold", 0.01)
                )
                method = getattr(experiment, "analysis_config", {}).get("method")

                for metric_results in results.get("metrics", {}).values():
                    for result in metric_results.values():
                        if method == AnalysisMethod.BAYESIAN:
                            prob_improvement = 1 - float(result.get("p_value", 0))
                            if (
                                prob_improvement > (1 - stopping_threshold)
                                or prob_improvement < stopping_threshold
                            ):
                                await self.stop_experiment(
                                    experiment,
                                    reason=f"Sequential stopping criterion met: probability of improvement = {prob_improvement:.3f}",
                                )
                                return
                        else:
                            p_value = float(result.get("p_value", 1))
                            if p_value < stopping_threshold:
                                await self.stop_experiment(
                                    experiment,
                                    reason=f"Sequential stopping criterion met: p-value = {p_value:.3f}",
                                )
                                return

            if "significance_threshold" in conditions:
                significance_threshold = float(conditions["significance_threshold"])
                for metric_results in results.get("metrics", {}).values():
                    for result in metric_results.values():
                        p_value = float(result.get("p_value", 1))
                        if p_value <= significance_threshold:
                            await self.stop_experiment(
                                experiment,
                                reason=f"Reached statistical significance (p-value: {p_value:.3f})",
                            )
                            return

            if "max_duration_hours" in conditions:
                max_duration = int(conditions["max_duration_hours"])
                if experiment.started_at:
                    duration = datetime.utcnow() - experiment.started_at
                    if duration.total_seconds() / 3600 >= max_duration:
                        await self.stop_experiment(experiment, reason="Reached maximum duration")
                        return

        except Exception as e:
            logger.error(
                f"Error checking auto-stop conditions for experiment {experiment.id}: {str(e)}"
            )

    async def stop_experiment(self, experiment: Experiment, reason: Optional[str] = None) -> None:
        """Stop an experiment and run final analysis"""
        try:
            setattr(experiment, "status", ExperimentStatus.COMPLETED)
            setattr(experiment, "ended_at", datetime.utcnow())
            setattr(experiment, "stopped_reason", reason)
            self.db.commit()

            exp_id = str(experiment.id)
            if exp_id in self.scheduled_tasks:
                self.scheduled_tasks[exp_id].cancel()
                del self.scheduled_tasks[exp_id]

            await self.experiment_service.analyze_results(exp_id)

            await self.experiment_service.data_service.record_event(
                experiment_id=exp_id, event_data={"event_type": "stop", "reason": reason}
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error stopping experiment {experiment.id}: {str(e)}")

    async def check_guardrails(self, experiment: Experiment) -> None:
        """Check guardrail metrics for an experiment"""
        try:
            for guardrail in experiment.guardrail_metrics:
                metric_data = await self.experiment_service.data_service.get_metric_data(
                    experiment_id=str(experiment.id), metric_name=guardrail.metric_name
                )

                model_guardrail = GuardrailMetric(
                    experiment_id=str(experiment.id),
                    metric_name=guardrail.metric_name,
                    threshold=guardrail.threshold,
                    operator=GuardrailOperator(guardrail.operator),
                )

                if self.is_guardrail_violated(metric_data, model_guardrail):
                    await self.handle_guardrail_violation(experiment, model_guardrail)

        except Exception as e:
            logger.error(f"Error checking guardrails for experiment {experiment.id}: {str(e)}")

    async def handle_guardrail_violation(
        self, experiment: Experiment, guardrail: GuardrailMetric
    ) -> None:
        """Handle a guardrail violation"""
        reason = f"Guardrail violation: {guardrail.metric_name} {guardrail.operator} {guardrail.threshold}"
        await self.stop_experiment(experiment, reason=reason)

        await self.experiment_service.data_service.record_event(
            experiment_id=str(experiment.id),
            event_data={
                "event_type": "guardrail_violation",
                "metric_name": guardrail.metric_name,
                "threshold": float(guardrail.threshold),
                "operator": str(guardrail.operator),
            },
        )

        logger.warning(
            f"Guardrail violation in experiment {experiment.id}: {guardrail.metric_name}"
        )

    def schedule_automated_analysis(self, experiment: Experiment) -> None:
        """Schedule automated analysis for an experiment"""
        interval = experiment.parameters.get("auto_analyze_interval")
        if not interval:
            return

        async def run_periodic_analysis() -> None:
            while True:
                await asyncio.sleep(interval)
                await self.experiment_service.analyze_results(str(experiment.id))

        task = asyncio.create_task(run_periodic_analysis())
        self.scheduled_tasks[str(experiment.id)] = task
