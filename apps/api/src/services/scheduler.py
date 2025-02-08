from typing import Dict
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session

from ..db.base import Experiment
from ..models.experiment import ExperimentStatus, GuardrailMetric
from .experiments import ExperimentService

class ExperimentScheduler:
    def __init__(
        self,
        experiment_service: ExperimentService,
        db: Session,
        check_interval: int = 60
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
        
        experiments = self.db.query(Experiment).filter(
            Experiment.status.in_([
                ExperimentStatus.DRAFT,
                ExperimentStatus.RUNNING
            ])
        ).all()
        
        for experiment in experiments:
            if (experiment.status == ExperimentStatus.DRAFT and 
                experiment.start_time and 
                experiment.start_time <= now):
                await self.start_experiment(experiment)
            
            elif (experiment.status == ExperimentStatus.RUNNING and 
                  experiment.end_time and 
                  experiment.end_time <= now):
                await self.stop_experiment(experiment)
            
            elif experiment.status == ExperimentStatus.RUNNING:
                await self.check_guardrails(experiment)

    async def start_experiment(self, experiment: Experiment):
        """Start an experiment and schedule automated analysis if needed"""
        try:
            experiment.status = ExperimentStatus.RUNNING
            experiment.started_at = datetime.utcnow()
            self.db.commit()
            
            if experiment.parameters.get('auto_analyze_interval'):
                self.schedule_automated_analysis(experiment)
            
        except Exception as e:
            self.db.rollback()
            print(f"Error starting experiment {experiment.id}: {str(e)}")

    async def stop_experiment(self, experiment: Experiment):
        """Stop an experiment and run final analysis"""
        try:
            experiment.status = ExperimentStatus.COMPLETED
            experiment.ended_at = datetime.utcnow()
            self.db.commit()
            
            if experiment.id in self.scheduled_tasks:
                self.scheduled_tasks[experiment.id].cancel()
                del self.scheduled_tasks[experiment.id]
            
            await self.experiment_service.analyze_results(experiment.id)
            
        except Exception as e:
            self.db.rollback()
            print(f"Error stopping experiment {experiment.id}: {str(e)}")

    async def check_guardrails(self, experiment: Experiment):
        """Check guardrail metrics for an experiment"""
        try:
            for guardrail in experiment.guardrail_metrics:
                metric_data = await self.experiment_service.get_metric_data(
                    experiment_id=experiment.id,
                    metric_name=guardrail.metric_name
                )
                
                if self.is_guardrail_violated(metric_data, guardrail):
                    await self.handle_guardrail_violation(experiment, guardrail)
                    
        except Exception as e:
            print(f"Error checking guardrails for experiment {experiment.id}: {str(e)}")

    def is_guardrail_violated(self, metric_data: Dict, guardrail: GuardrailMetric) -> bool:
        """Check if a guardrail metric is violated"""
        for variant_id, values in metric_data.items():
            if not values:
                continue
                
            metric_value = sum(values) / len(values)
            
            if guardrail.operator == 'gt' and metric_value > guardrail.threshold:
                return True
            elif guardrail.operator == 'lt' and metric_value < guardrail.threshold:
                return True
            elif guardrail.operator == 'gte' and metric_value >= guardrail.threshold:
                return True
            elif guardrail.operator == 'lte' and metric_value <= guardrail.threshold:
                return True
                
        return False

    async def handle_guardrail_violation(self, experiment: Experiment, guardrail: GuardrailMetric):
        """Handle a guardrail violation"""
        await self.stop_experiment(experiment)
        
        await self.experiment_service.record_event(
            experiment_id=experiment.id,
            event_data={
                'event_type': 'guardrail_violation',
                'metric_name': guardrail.metric_name,
                'threshold': guardrail.threshold,
                'operator': guardrail.operator
            }
        )
        
        # TODO: Implement notification system
        print(f"Guardrail violation in experiment {experiment.id}: {guardrail.metric_name}")

    def schedule_automated_analysis(self, experiment: Experiment):
        """Schedule automated analysis for an experiment"""
        interval = experiment.parameters.get('auto_analyze_interval')
        if not interval:
            return
            
        async def run_periodic_analysis():
            while True:
                await asyncio.sleep(interval)
                await self.experiment_service.analyze_results(experiment.id)
        
        task = asyncio.create_task(run_periodic_analysis())
        self.scheduled_tasks[experiment.id] = task