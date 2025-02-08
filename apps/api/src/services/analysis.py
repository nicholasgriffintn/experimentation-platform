from typing import Dict, List, Tuple
import numpy as np
from scipy import stats
from dataclasses import dataclass
from enum import Enum

class MetricType(str, Enum):
    CONTINUOUS = "continuous"
    BINARY = "binary"
    COUNT = "count"
    RATIO = "ratio"

@dataclass
class ExperimentResult:
    metric_name: str
    control_mean: float
    variant_mean: float
    relative_difference: float
    p_value: float
    confidence_interval: Tuple[float, float]
    sample_size: Dict[str, int]
    power: float
    is_significant: bool

class StatisticalAnalysisService:
    # TODO: This is a simple implementation for now, I'll work on this over time.
    def __init__(self, min_sample_size: int = 100, confidence_level: float = 0.95):
        self.min_sample_size = min_sample_size
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    async def analyze_experiment(
        self,
        control_data: List[float],
        variant_data: List[float],
        metric_type: MetricType,
        metric_name: str
    ) -> ExperimentResult:
        """Perform statistical analysis on experiment data"""
        
        if len(control_data) < self.min_sample_size or len(variant_data) < self.min_sample_size:
            raise ValueError(f"Insufficient sample size. Minimum required: {self.min_sample_size}")

        control_mean = np.mean(control_data)
        variant_mean = np.mean(variant_data)
        relative_diff = ((variant_mean - control_mean) / control_mean) * 100

        if metric_type == MetricType.BINARY:
            p_value = self._calculate_binary_significance(control_data, variant_data)
            ci = self._calculate_binary_confidence_interval(control_data, variant_data)
        else:
            t_stat, p_value = stats.ttest_ind(control_data, variant_data)
            ci = self._calculate_continuous_confidence_interval(control_data, variant_data)

        power = self._calculate_power(control_data, variant_data)

        return ExperimentResult(
            metric_name=metric_name,
            control_mean=control_mean,
            variant_mean=variant_mean,
            relative_difference=relative_diff,
            p_value=p_value,
            confidence_interval=ci,
            sample_size={
                "control": len(control_data),
                "variant": len(variant_data)
            },
            power=power,
            is_significant=p_value < self.alpha
        )

    def _calculate_binary_significance(self, control_data: List[float], variant_data: List[float]) -> float:
        """Calculate significance for binary metrics using chi-square test"""
        control_success = sum(control_data)
        variant_success = sum(variant_data)
        
        contingency_table = np.array([
            [control_success, len(control_data) - control_success],
            [variant_success, len(variant_data) - variant_success]
        ])
        
        _, p_value = stats.chi2_contingency(contingency_table)
        return p_value

    def _calculate_binary_confidence_interval(
        self,
        control_data: List[float],
        variant_data: List[float]
    ) -> Tuple[float, float]:
        """Calculate confidence interval for binary metrics"""
        control_prop = np.mean(control_data)
        variant_prop = np.mean(variant_data)
        
        se = np.sqrt(
            (control_prop * (1 - control_prop) / len(control_data)) +
            (variant_prop * (1 - variant_prop) / len(variant_data))
        )
        
        z_score = stats.norm.ppf(1 - self.alpha / 2)
        margin_error = z_score * se
        
        return (variant_prop - control_prop - margin_error,
                variant_prop - control_prop + margin_error)

    def _calculate_continuous_confidence_interval(
        self,
        control_data: List[float],
        variant_data: List[float]
    ) -> Tuple[float, float]:
        """Calculate confidence interval for continuous metrics"""
        control_mean = np.mean(control_data)
        variant_mean = np.mean(variant_data)
        
        control_var = np.var(control_data, ddof=1)
        variant_var = np.var(variant_data, ddof=1)
        
        se = np.sqrt(
            (control_var / len(control_data)) +
            (variant_var / len(variant_data))
        )
        
        t_score = stats.t.ppf(1 - self.alpha / 2, len(control_data) + len(variant_data) - 2)
        margin_error = t_score * se
        
        return (variant_mean - control_mean - margin_error,
                variant_mean - control_mean + margin_error)

    def _calculate_power(self, control_data: List[float], variant_data: List[float]) -> float:
        """Calculate statistical power"""
        effect_size = self._cohens_d(control_data, variant_data)
        return stats.power.TTestIndPower().power(
            effect_size=effect_size,
            nobs=min(len(control_data), len(variant_data)),
            alpha=self.alpha
        )

    def _cohens_d(self, control_data: List[float], variant_data: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        n1, n2 = len(control_data), len(variant_data)
        var1, var2 = np.var(control_data, ddof=1), np.var(variant_data, ddof=1)
        
        pooled_sd = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        
        return abs(np.mean(control_data) - np.mean(variant_data)) / pooled_sd

    async def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        power: float = 0.8
    ) -> int:
        """Calculate required sample size for desired statistical power"""
        effect_size = minimum_detectable_effect / np.sqrt(
            baseline_rate * (1 - baseline_rate)
        )
        
        analysis = stats.power.TTestIndPower()
        sample_size = analysis.solve_power(
            effect_size=effect_size,
            power=power,
            alpha=self.alpha
        )
        
        return int(np.ceil(sample_size))