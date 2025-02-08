import numpy as np

from .plotting import plot_power_curve
from .calculations import calculate_power

def display_results(self):
    """Returns the results of the A/B test."""

    effect_sizes = np.arange(0, 0.2, 0.005)
    powers = [
        calculate_power(
            self.prop_null,
            self.trials_null,
            self.trials_alt,
            es,
            self.alpha,
            self.alt_hypothesis,
        )
        for es in effect_sizes
    ]
    plots =  plot_power_curve(effect_sizes, powers, self.prop_alt - self.prop_null)

    results = {
        "version_a": {
            "success": self.success_null,
            "trials": self.trials_null,
            "proportion": self.prop_null,
        },
        "version_b": {
            "success": self.success_alt,
            "trials": self.trials_alt,
            "proportion": self.prop_alt,
        },
        "statistic": self.stat,
        "pvalue": self.pvalue,
        "significant": self.pvalue < self.alpha,
        "plots": plots,
    }
    return results
