import numpy as np
import scipy.stats as st


def calculate_pvalue(stat, alt_hypothesis, alpha):
    """Calculate the p-value based on the test statistic and the hypothesis type."""
    if alt_hypothesis == "one_tailed":
        return 1 - st.norm.cdf(np.abs(stat)) if stat > 0 else st.norm.cdf(stat)
    elif alt_hypothesis == "two_tailed":
        return 2 * (1 - st.norm.cdf(np.abs(stat)))


def calculate_power(
    prop_null, trials_null, trials_alt, effect_size, alpha, alt_hypothesis
):
    """Calculate the power of the test given a specific effect size."""
    se_pooled = np.sqrt(
        prop_null * (1 - prop_null) * (1 / trials_null + 1 / trials_alt)
    )
    z_alpha = (
        st.norm.ppf(1 - alpha / 2)
        if alt_hypothesis == "two_tailed"
        else st.norm.ppf(1 - alpha)
    )
    z_effect = effect_size / se_pooled
    return 1 - st.norm.cdf(z_alpha - z_effect)

def calculate_stat_pvalue(self, sequential, stopping_threshold):
    pooled_prop, se_pooled = calculate_pooled_prop_se(self)
    stat = (self.prop_alt - self.prop_null) / se_pooled

    if sequential:
        return self.perform_sequential_testing(stopping_threshold)
    else:
        pvalue = calculate_pvalue(stat, self.alt_hypothesis, self.alpha)
        return stat, pvalue

def calculate_pooled_prop_se(self):
    pooled_prop = (self.success_null + self.success_alt) / (self.trials_null + self.trials_alt)
    se_pooled = np.sqrt(
        pooled_prop * (1 - pooled_prop) * (1 / self.trials_null + 1 / self.trials_alt)
    )
    return pooled_prop, se_pooled
