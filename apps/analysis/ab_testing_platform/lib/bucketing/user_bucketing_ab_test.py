from .frequentist_test import run_frequentist_test
from .bayesian_test import run_bayesian_test
from .utils import assign_to_group


class UserBucketingABTest:
    """
    A/B Testing with User Bucketing for both Frequentist and Bayesian approaches. Designed to be used
    with data already in the data warehouse.

    Example usage:

    user_data = [
        {'user_id': 1, 'event': 1}, {'user_id': 2, 'event': 0}, {'user_id': 3, 'event': 1},
        {'user_id': 4, 'event': 1}, {'user_id': 5, 'event': 0}, {'user_id': 6, 'event': 0},
        # More users...
    ]
    group_buckets = {
        'control': range(0, 50),
        'test1': range(50, 75),
        'test2': range(75, 100)
    }
    ab_test = UserBucketingABTest(method='frequentist', alpha=0.05)
    result = ab_test.run_experiment(user_data, group_buckets)

    Parameters
    ----------
    method : str
        'frequentist' or 'bayesian' to specify which A/B testing method to use.

    alpha : float, default=0.05
        Significance level for Frequentist A/B testing.

    prior_successes : int, optional
        Number of prior successes for Bayesian A/B testing.

    prior_trials : int, optional
        Number of prior trials for Bayesian A/B testing.

    num_samples : int, optional
        Number of posterior samples for Bayesian A/B testing.

    sequential : bool, optional
        Whether to use sequential testing.

    stopping_threshold : float, optional
        The threshold for stopping the experiment early if sequential testing is used.
    """

    def __init__(
        self,
        method,
        alpha=0.05,
        prior_successes=30,
        prior_trials=100,
        num_samples=2000,
        sequential=False,
        stopping_threshold=None,
    ):
        self.method = method
        self.alpha = alpha
        self.prior_successes = prior_successes
        self.prior_trials = prior_trials
        self.num_samples = num_samples
        self.sequential = sequential
        self.stopping_threshold = stopping_threshold

    def run_experiment(self, user_data, group_buckets):
        """
        Run the A/B test experiment on the given user data.

        Parameters
        ----------
        user_data : list of dicts
            A list of dictionaries where each dictionary represents a user and contains the following keys:
            - 'user_id': The unique identifier for the user.
            - 'event': 1 for success (e.g., clicked), 0 for failure (e.g., did not click).

        group_buckets : dict
            A dictionary where keys are group names and values are ranges of buckets assigned to each group.

        Returns
        -------
        dict
            A dictionary containing the test results (statistic, p-value, or uplift distribution).
        """
        group_results = {
            group: {"success": 0, "trials": 0} for group in group_buckets.keys()
        }

        # Assign users to groups and record their results
        for user in user_data:
            group = assign_to_group(user["user_id"], group_buckets)
            group_results[group]["trials"] += 1
            group_results[group]["success"] += user["event"]

        if self.method == "frequentist":
            return run_frequentist_test(
                group_results, self.alpha, self.sequential, self.stopping_threshold
            )
        elif self.method == "bayesian":
            return run_bayesian_test(
                group_results,
                self.prior_successes,
                self.prior_trials,
                self.num_samples,
                self.sequential,
                self.stopping_threshold,
            )
        else:
            raise ValueError(f"Unknown method: {self.method}")
