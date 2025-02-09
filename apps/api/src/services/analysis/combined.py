from typing import Dict, List, Optional
from dataclasses import dataclass

from .frequentist import StatisticalAnalysisService, ExperimentResult
from .bayesian import BayesianAnalysisService
from .correction import MultipleTestingCorrection

@dataclass
class CombinedAnalysisResult:
    """Combined results from both frequentist and Bayesian analysis"""
    metric_name: str
    frequentist_results: ExperimentResult
    bayesian_results: Dict
    corrected_p_value: Optional[float] = None

class CombinedAnalysisService:
    """Service that combines frequentist and Bayesian analysis approaches"""
    
    def __init__(
        self,
        frequentist_service: StatisticalAnalysisService,
        bayesian_service: BayesianAnalysisService,
        correction_service: MultipleTestingCorrection
    ):
        self.frequentist_service = frequentist_service
        self.bayesian_service = bayesian_service
        self.correction_service = correction_service
        
    def analyze_experiment(
        self,
        control_data: List[float],
        variant_data: List[float],
        metric_name: str,
        metric_type: str = "continuous",
        alpha: float = 0.05,
        correction_method: Optional[str] = None
    ) -> CombinedAnalysisResult:
        """
        Analyze experiment data using both frequentist and Bayesian approaches
        
        Parameters
        ----------
        control_data : List[float]
            Data from control group
        variant_data : List[float]
            Data from variant group
        metric_name : str
            Name of the metric being analyzed
        metric_type : str
            Type of metric ('binary', 'continuous', 'ratio', 'count')
        alpha : float
            Significance level for frequentist analysis
        correction_method : Optional[str]
            Multiple testing correction method (None, 'fdr_bh', 'holm')
            
        Returns
        -------
        CombinedAnalysisResult
            Combined results from both analysis approaches
        """
        freq_results = self.frequentist_service.analyze_experiment(
            control_data=control_data,
            variant_data=variant_data,
            metric_type=metric_type,
            alpha=alpha
        )
        
        if metric_type == "binary":
            bayes_results = self.bayesian_service.analyze_binary_metric(
                control_data=control_data,
                variant_data=variant_data
            )
        else:
            bayes_results = self.bayesian_service.analyze_continuous_metric(
                control_data=control_data,
                variant_data=variant_data
            )
            
        corrected_p_value = None
        if correction_method and freq_results.p_value is not None:
            corrected_p_values = self.correction_service.apply_correction(
                [freq_results.p_value],
                method=correction_method
            )
            corrected_p_value = corrected_p_values[0]
            
        return CombinedAnalysisResult(
            metric_name=metric_name,
            frequentist_results=freq_results,
            bayesian_results=bayes_results,
            corrected_p_value=corrected_p_value
        )
        
    def analyze_multiple_metrics(
        self,
        metrics_data: Dict[str, Dict],
        metric_types: Dict[str, str],
        alpha: float = 0.05,
        correction_method: str = "fdr_bh"
    ) -> Dict[str, CombinedAnalysisResult]:
        """
        Analyze multiple metrics with correction for multiple testing
        
        Parameters
        ----------
        metrics_data : Dict[str, Dict]
            Dictionary mapping metric names to their data
            Each data dict should have 'control' and 'variant' lists
        metric_types : Dict[str, str]
            Dictionary mapping metric names to their types
        alpha : float
            Significance level for frequentist analysis
        correction_method : str
            Multiple testing correction method ('fdr_bh' or 'holm')
            
        Returns
        -------
        Dict[str, CombinedAnalysisResult]
            Dictionary mapping metric names to their combined analysis results
        """
        uncorrected_results = {}
        p_values = []
        
        for metric_name, data in metrics_data.items():
            metric_type = metric_types[metric_name]
            result = self.analyze_experiment(
                control_data=data['control'],
                variant_data=data['variant'],
                metric_name=metric_name,
                metric_type=metric_type,
                alpha=alpha
            )
            uncorrected_results[metric_name] = result
            if result.frequentist_results.p_value is not None:
                p_values.append(result.frequentist_results.p_value)
                
        if p_values:
            corrected_p_values = self.correction_service.apply_correction(
                p_values,
                method=correction_method
            )
            
            for i, (metric_name, result) in enumerate(uncorrected_results.items()):
                if result.frequentist_results.p_value is not None:
                    result.corrected_p_value = corrected_p_values[i]
                    
        return uncorrected_results 