import numpy as np

from .validation import validate_hypothesis
from .calculations import calculate_pvalue, calculate_stat_pvalue
from .results import display_results


class FrequentistABTest:
    """
    Frequentist A/B Testing aka Two sample proportion test.

    Example usage:

    ab_test = FrequentistABTest(alpha=0.05, alt_hypothesis='two_tailed')
    ab_test.run_experiment(success_null=300, trials_null=1000, success_alt=350, trials_alt=1000)
    ab_test.plot_power_curve()

    Parameters
    ----------
    alpha : float, default=0.05
        Significance level or Type I error rate.

    alt_hypothesis : str, default='one_tailed'
        Defines the hypothesis test.

        * 'one_tailed': one-tailed hypothesis test.
        * 'two_tailed': two-tailed hypothesis test.
    """

    def __init__(self, alpha=0.05, alt_hypothesis="one_tailed"):
        self.alpha = alpha
        self.alt_hypothesis = alt_hypothesis.lower()
        validate_hypothesis(self.alt_hypothesis, self.alpha)

    def run_experiment(
        self,
        success_null,
        trials_null,
        success_alt,
        trials_alt,
        sequential=False,
        stopping_threshold=0.05,
    ):
        """
        Conduct A/B test and calculate the statistical significance.

        Parameters
        ----------
        success_null : int
            Successful trials (Version A).
        trials_null : int
            Total trials for Version A.
        success_alt : int
            Successful trials (Version B).
        trials_alt : int
            Total trials for Version B.
        sequential : bool, default=False
            Whether to perform sequential testing.
        stopping_threshold : float, default=0.05
            P-value threshold for stopping the sequential test

        Returns
        -------
        stat : float
            Z statistic (or t-statistic in small sample cases).
        pvalue : float
            The probability of observing the test statistic as extreme or more extreme than observed.
        """
        self.success_null = success_null
        self.trials_null = trials_null
        self.success_alt = success_alt
        self.trials_alt = trials_alt

        self.prop_null = success_null / trials_null
        self.prop_alt = success_alt / trials_alt

        self.stat, self.pvalue = calculate_stat_pvalue(self, sequential, stopping_threshold)

        return display_results(self)

    def perform_sequential_testing(self, stopping_threshold):
        for i in range(1, self.trials_null + self.trials_alt + 1):
            success_null_i = int(i * (self.success_null / (self.trials_null + self.trials_alt)))
            success_alt_i = int(i * (self.success_alt / (self.trials_null + self.trials_alt)))

            prop_null_i = success_null_i / i
            prop_alt_i = success_alt_i / i

            pooled_prop_i = (success_null_i + success_alt_i) / (2 * i)
            se_pooled_i = np.sqrt(pooled_prop_i * (1 - pooled_prop_i) * (2 / i))

            if se_pooled_i == 0:
                stat_i = np.nan
            else:
                stat_i = (prop_alt_i - prop_null_i) / se_pooled_i
            pvalue_i = calculate_pvalue(stat_i, self.alt_hypothesis, self.alpha)
            self.pvalue = pvalue_i
            self.stat = stat_i

            if pvalue_i < stopping_threshold:
                print(f"Stopping early at trial {i} with p-value {pvalue_i:.4f}")
                return stat_i, pvalue_i

        return self.stat, self.pvalue
