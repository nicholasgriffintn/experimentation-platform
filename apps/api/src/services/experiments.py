from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from .data import IcebergDataService
from .analysis import StatisticalAnalysisService

class ExperimentType(str, Enum):
    AB = "ab"
    ABN = "abn"
    MVT = "mvt"
    FEATURE_FLAG = "feature_flag"

class VariantType(str, Enum):
    CONTROL = "control"
    TREATMENT = "treatment"
    FEATURE_FLAG = "feature_flag"

class TargetingType(str, Enum):
    USER_ID = "user_id"
    SESSION_ID = "session_id"
    CUSTOM = "custom"

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
        data_service: IcebergDataService,
        stats_service: StatisticalAnalysisService,
        cache_service: Optional[Any] = None
    ):
        self.data_service = data_service
        self.stats_service = stats_service
        self.cache_service = cache_service

    async def initialize_experiment(
        self,
        experiment_id: str,
        config: Dict
    ) -> None:
        """Initialize a new experiment with required infrastructure"""
        await self.data_service.initialize_experiment_tables(experiment_id)
        
        if self.cache_service:
            await self.cache_service.set_experiment_config(experiment_id, config)

    async def assign_variant(
        self,
        experiment_id: str,
        user_context: Dict,
        targeting_type: TargetingType = TargetingType.USER_ID
    ) -> VariantConfig:
        """Assign a variant to a user based on targeting rules"""
        config = await self._get_experiment_config(experiment_id)
        
        if not self._meets_targeting_rules(user_context, config.get('targeting_rules', {})):
            return None

        assignment_key = self._get_assignment_key(user_context, targeting_type)
        variant = await self._get_consistent_assignment(
            experiment_id,
            assignment_key,
            config['variants']
        )

        await self.data_service.assign_variant(
            experiment_id=experiment_id,
            user_id=user_context.get('user_id'),
            variant_id=variant.id,
            context=user_context
        )

        return variant

    async def record_exposure(
        self,
        experiment_id: str,
        user_context: Dict,
        metadata: Optional[Dict] = None
    ) -> None:
        """Record an exposure event for the experiment"""
        await self.data_service.record_event(
            experiment_id=experiment_id,
            event_data={
                'user_id': user_context.get('user_id'),
                'event_type': 'exposure',
                'metadata': metadata or {}
            }
        )

    async def record_metric(
        self,
        experiment_id: str,
        metric_name: str,
        value: float,
        user_context: Dict,
        metadata: Optional[Dict] = None
    ) -> None:
        """Record a metric measurement for the experiment"""
        variant = await self._get_user_variant(experiment_id, user_context)
        if not variant:
            return

        await self.data_service.record_metric(
            experiment_id=experiment_id,
            metric_data={
                'metric_name': metric_name,
                'metric_value': value,
                'variant_id': variant.id,
                'user_id': user_context.get('user_id'),
                'metadata': metadata or {}
            }
        )

    async def analyze_results(
        self,
        experiment_id: str,
        metrics: Optional[List[str]] = None
    ) -> Dict:
        """Analyze current experiment results"""
        config = await self._get_experiment_config(experiment_id)
        metrics_to_analyze = metrics or [m.name for m in config['metrics']]
        
        results = {}
        for metric_name in metrics_to_analyze:
            metric_data = await self._get_metric_data(experiment_id, metric_name)
            
            control_data = metric_data.get('control', [])
            for variant_id, variant_data in metric_data.items():
                if variant_id == 'control':
                    continue
                    
                analysis_result = await self.stats_service.analyze_experiment(
                    control_data=control_data,
                    variant_data=variant_data,
                    metric_type=config['metrics'][metric_name].type,
                    metric_name=metric_name
                )
                
                results[f"{metric_name}_{variant_id}"] = analysis_result

        await self.data_service.record_results(
            experiment_id=experiment_id,
            results_data=results
        )

        return results

    def _meets_targeting_rules(self, user_context: Dict, targeting_rules: Dict) -> bool:
        """Check if user meets targeting rules"""
        for rule_key, rule_value in targeting_rules.items():
            if rule_key not in user_context:
                return False
            if user_context[rule_key] != rule_value:
                return False
        return True

    async def _get_consistent_assignment(
        self,
        experiment_id: str,
        assignment_key: str,
        variants: List[VariantConfig]
    ) -> VariantConfig:
        """Get consistent variant assignment based on hash"""
        import hashlib
        
        hash_input = f"{experiment_id}:{assignment_key}".encode()
        hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)
        
        normalized_hash = hash_value / 2**256
        
        cumulative_split = 0
        for variant in variants:
            cumulative_split += variant.traffic_percentage
            if normalized_hash < cumulative_split:
                return variant
                
        return variants[-1]

    async def _get_metric_data(
        self,
        experiment_id: str,
        metric_name: str
    ) -> Dict[str, List[float]]:
        """Get metric data grouped by variant"""
        metric_history = await self.data_service.get_metric_history(
            experiment_id=experiment_id,
            metric_name=metric_name
        )
        
        from itertools import groupby
        from operator import itemgetter
        
        grouped_data = {}
        for variant_id, group in groupby(metric_history, key=itemgetter('variant_id')):
            grouped_data[variant_id] = [item['metric_value'] for item in group]
            
        return grouped_data