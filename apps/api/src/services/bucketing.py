import hashlib
from typing import Dict, Optional

from ..models.experiments_model import ExperimentType, VariantConfig


class BucketingService:
    """Service for consistently assigning users to experiment variants"""

    def __init__(self, bucket_count: int = 100):
        """
        Initialize the bucketing service.

        Parameters
        ----------
        bucket_count : int, default=100
            The total number of buckets (determines traffic allocation granularity)
        """
        self.bucket_count = bucket_count

    def _get_user_bucket(self, user_id: str, experiment_id: str) -> int:
        """
        Get a consistent bucket number for a user in a specific experiment.
        Uses a hash of the user_id and experiment_id to ensure:
        1. Same user gets same variant in an experiment
        2. Same user can get different variants in different experiments
        3. Assignment is uniformly distributed

        Parameters
        ----------
        user_id : str
            The unique identifier for a user
        experiment_id : str
            The unique identifier for the experiment

        Returns
        -------
        int
            A bucket number between 0 and bucket_count-1
        """
        hash_input = f"{experiment_id}:{user_id}".encode("utf-8")
        hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)
        return hash_value % self.bucket_count

    def assign_variant(
        self,
        user_id: str,
        experiment_id: str,
        variants: list[VariantConfig],
        experiment_type: ExperimentType,
        traffic_allocation: float = 100.0,
    ) -> Optional[VariantConfig]:
        """
        Assign a user to a variant in an experiment.

        Parameters
        ----------
        user_id : str
            The unique identifier for a user
        experiment_id : str
            The unique identifier for the experiment
        variants : list[VariantConfig]
            List of possible variants
        experiment_type : ExperimentType
            Type of experiment (affects assignment logic)
        traffic_allocation : float, default=100.0
            Percentage of traffic to include in experiment

        Returns
        -------
        Optional[VariantConfig]
            The assigned variant, or None if user is not included in experiment
        """
        inclusion_bucket = self._get_user_bucket(user_id, f"{experiment_id}:inclusion")
        if (inclusion_bucket / self.bucket_count * 100) > traffic_allocation:
            return None

        bucket = self._get_user_bucket(user_id, experiment_id)

        total_allocation = sum(v.traffic_percentage for v in variants)
        if total_allocation != 100:
            scale_factor = 100 / total_allocation
            cumulative = 0
            for variant in variants:
                variant_buckets = (
                    variant.traffic_percentage * scale_factor / 100
                ) * self.bucket_count
                upper_bound = cumulative + variant_buckets
                if bucket < upper_bound:
                    return variant
                cumulative = upper_bound
        else:
            cumulative = 0
            for variant in variants:
                variant_buckets = (variant.traffic_percentage / 100) * self.bucket_count
                upper_bound = cumulative + variant_buckets
                if bucket < upper_bound:
                    return variant
                cumulative = upper_bound

        return variants[0] if variants else None

    def get_assignment_ranges(self, variants: list[VariantConfig]) -> Dict[str, range]:
        """
        Get the bucket ranges for each variant based on their traffic allocation.
        Useful for debugging and visualization.

        Parameters
        ----------
        variants : list[VariantConfig]
            List of variants with traffic percentages

        Returns
        -------
        Dict[str, range]
            Dictionary mapping variant IDs to their bucket ranges
        """
        ranges = {}
        total_allocation = sum(v.traffic_percentage for v in variants)
        scale_factor = 100 / total_allocation

        cumulative = 0
        for variant in variants:
            variant_buckets = int(
                (variant.traffic_percentage * scale_factor / 100) * self.bucket_count
            )
            ranges[variant.id] = range(cumulative, cumulative + variant_buckets)
            cumulative += variant_buckets

        return ranges
