import asyncio
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from ..db.base import Experiment
from ..models.analysis_model import AnalysisMethod
from ..models.experiments_model import ExperimentStatus
from ..models.guardrails_model import GuardrailMetric
from ..utils.logger import logger
from .experiments import ExperimentService


class ExperimentScheduler:
    def __init__(
        self, experiment_service: ExperimentService, db: Session, check_interval: int = 60
    ):
        self.experiment_service = experiment_service
        self.db = db
        self.check_interval = check_interval
        self.running = False
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start the scheduler"""
        self.running = True
        while self.running:
            await self.check_experiments()
            await asyncio.sleep(self.check_interval)

    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        for task in self.scheduled_tasks.values():
            task.cancel()

    async def check_experiments(self):
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

    async def start_experiment(self, experiment: Experiment):
        """Start an experiment and schedule automated analysis if needed"""
        try:
            if experiment.ramp_up_period:
                await self._apply_ramp_up_traffic(experiment)
            else:
                experiment.status = ExperimentStatus.RUNNING

            experiment.started_at = datetime.utcnow()
            self.db.commit()

            if experiment.parameters.get("auto_analyze_interval"):
                self.schedule_automated_analysis(experiment)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error starting experiment {experiment.id}: {str(e)}")

    async def _apply_ramp_up_traffic(self, experiment: Experiment):
        """Apply initial traffic allocation for ramp-up"""
        try:
            initial_traffic_percentage = 10
            experiment.traffic_allocation = initial_traffic_percentage
            experiment.status = ExperimentStatus.RUNNING
            self.db.commit()

            total_hours = experiment.ramp_up_period
            steps = 5
            hours_per_step = total_hours / steps

            for step in range(1, steps + 1):
                self.scheduled_tasks[f"{experiment.id}_rampup_{step}"] = asyncio.create_task(
                    self._schedule_traffic_increase(
                        experiment_id=experiment.id,
                        delay_hours=hours_per_step * step,
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
    ):
        """Schedule a traffic increase after a delay"""
        await asyncio.sleep(delay_hours * 3600)

        experiment = (
            self.db.query(Experiment)
            .filter(Experiment.id == experiment_id, Experiment.status == ExperimentStatus.RUNNING)
            .first()
        )

        if experiment:
            try:
                experiment.traffic_allocation = target_percentage
                self.db.commit()

                await self.experiment_service.record_event(
                    experiment_id=experiment_id,
                    event_data={
                        "event_type": "traffic_allocation_update",
                        "traffic_allocation": target_percentage,
                    },
                )
            except Exception as e:
                logger.error(f"Error increasing traffic for experiment {experiment_id}: {str(e)}")

    async def check_auto_stop_conditions(self, experiment: Experiment):
        """Check if any auto-stop conditions are met"""
        conditions = experiment.auto_stop_conditions
        if not conditions:
            return

        try:
            if "min_sample_size" in conditions:
                sample_size = await self._get_experiment_sample_size(experiment)
                if sample_size >= conditions["min_sample_size"]:
                    await self.stop_experiment(experiment, reason="Reached target sample size")
                    return

            results = await self.experiment_service.analyze_results(experiment.id)

            if experiment.analysis_config.sequential_testing:
                stopping_threshold = experiment.analysis_config.stopping_threshold
                method = experiment.analysis_config.method

                for metric_results in results.get("metrics", {}).values():
                    for result in metric_results.values():
                        if method == AnalysisMethod.BAYESIAN:
                            prob_improvement = 1 - result.get("p_value", 0)
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
                            p_value = result.get("p_value", 1)
                            if p_value < stopping_threshold:
                                await self.stop_experiment(
                                    experiment,
                                    reason=f"Sequential stopping criterion met: p-value = {p_value:.3f}",
                                )
                                return

            if "significance_threshold" in conditions:
                for metric_results in results.get("metrics", {}).values():
                    for result in metric_results.values():
                        if result.get("p_value", 1) <= conditions["significance_threshold"]:
                            await self.stop_experiment(
                                experiment,
                                reason=f"Reached statistical significance (p-value: {result['p_value']:.3f})",
                            )
                            return

            if "max_duration_hours" in conditions:
                duration = datetime.utcnow() - experiment.started_at
                if duration.total_seconds() / 3600 >= conditions["max_duration_hours"]:
                    await self.stop_experiment(experiment, reason="Reached maximum duration")
                    return

        except Exception as e:
            logger.error(
                f"Error checking auto-stop conditions for experiment {experiment.id}: {str(e)}"
            )

    async def _get_experiment_sample_size(self, experiment: Experiment) -> int:
        """
        Get the current sample size of the experiment.
        Returns the size of the smallest variant group (control or treatment)
        to ensure we have sufficient data across all variants.
        """
        try:
            exposure_data = await self.experiment_service.data_service.get_exposure_data(
                experiment.id
            )
            if not exposure_data:
                return 0

            variant_sizes = {}
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

    async def stop_experiment(self, experiment: Experiment, reason: Optional[str] = None):
        """Stop an experiment and run final analysis"""
        try:
            experiment.status = ExperimentStatus.COMPLETED
            experiment.ended_at = datetime.utcnow()
            experiment.stopped_reason = reason
            self.db.commit()

            if experiment.id in self.scheduled_tasks:
                self.scheduled_tasks[experiment.id].cancel()
                del self.scheduled_tasks[experiment.id]

            await self.experiment_service.analyze_results(experiment.id)

            await self.experiment_service.data_service.record_event(
                experiment_id=experiment.id, event_data={"event_type": "stop", "reason": reason}
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error stopping experiment {experiment.id}: {str(e)}")

    async def check_guardrails(self, experiment: Experiment):
        """Check guardrail metrics for an experiment"""
        try:
            for guardrail in experiment.guardrail_metrics:
                metric_data = await self.experiment_service.get_metric_data(
                    experiment_id=experiment.id, metric_name=guardrail.metric_name
                )

                if self.is_guardrail_violated(metric_data, guardrail):
                    await self.handle_guardrail_violation(experiment, guardrail)

        except Exception as e:
            logger.error(f"Error checking guardrails for experiment {experiment.id}: {str(e)}")

    def is_guardrail_violated(self, metric_data: Dict, guardrail: GuardrailMetric) -> bool:
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

    async def handle_guardrail_violation(self, experiment: Experiment, guardrail: GuardrailMetric):
        """Handle a guardrail violation"""
        await self.stop_experiment(experiment)

        await self.experiment_service.record_event(
            experiment_id=experiment.id,
            event_data={
                "event_type": "guardrail_violation",
                "metric_name": guardrail.metric_name,
                "threshold": guardrail.threshold,
                "operator": guardrail.operator,
            },
        )

        logger.warning(
            f"Guardrail violation in experiment {experiment.id}: {guardrail.metric_name}"
        )

    def schedule_automated_analysis(self, experiment: Experiment):
        """Schedule automated analysis for an experiment"""
        interval = experiment.parameters.get("auto_analyze_interval")
        if not interval:
            return

        async def run_periodic_analysis():
            while True:
                await asyncio.sleep(interval)
                await self.experiment_service.analyze_results(experiment.id)

        task = asyncio.create_task(run_periodic_analysis())
        self.scheduled_tasks[experiment.id] = task
