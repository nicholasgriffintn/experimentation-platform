import pymc as pm
import numpy as np

from .utils import calculate_uplift
from .results import display_results


class BayesianABTest:
    """
    Bayesian A/B Testing using PyMC.

    Example usage:

    ab_test = BayesianABTest(prior_successes=30, prior_trials=100)
    ab_test.run_experiment(variant_a_successes=40, variant_a_trials=100,
                        variant_b_successes=50, variant_b_trials=100,
                        uplift_method='percent', num_samples=2000)

    Parameters
    ----------
    prior_successes : int
        Number of successful samples from prior data.

    prior_trials : int
        Number of total trials from prior data.
    """

    def __init__(self, prior_successes, prior_trials):
        self.prior_successes = prior_successes
        self.prior_trials = prior_trials
        self.prior_failures = prior_trials - prior_successes

    def run_experiment(
        self,
        variant_a_successes,
        variant_a_trials,
        variant_b_successes,
        variant_b_trials,
        uplift_method="percent",
        num_samples=2000,
        sequential=False,
        stopping_threshold=0.95,
    ):
        """
        Run Bayesian A/B test experiment and calculate uplift.

        Parameters
        ----------
        variant_a_successes : int
            Number of successful samples for variant A (control group).

        variant_a_trials : int
            Number of total trials for variant A.

        variant_b_successes : int
            Number of successful samples for variant B (treatment group).

        variant_b_trials : int
            Number of total trials for variant B.

        uplift_method : str, default='percent'
            Method for calculating uplift ('percent', 'ratio', or 'difference').

        num_samples : int, default=2000
            Number of posterior samples.

        sequential : bool, default=False
            Whether to perform sequential testing.

        stopping_threshold : float, default=0.95
            Posterior probability threshold for stopping the sequential test.
        """

        # Defining the Bayesian model using PyMC
        with pm.Model() as model:
            # Priors for variant A and B (Beta distributions with prior data)
            prior_a = pm.Beta(
                "prior_a", alpha=self.prior_successes + 1, beta=self.prior_failures + 1
            )
            prior_b = pm.Beta(
                "prior_b", alpha=self.prior_successes + 1, beta=self.prior_failures + 1
            )

            # Likelihoods (Binomial distributions) based on observed data for each variant
            likelihood_a = pm.Binomial(
                "likelihood_a",
                n=variant_a_trials,
                p=prior_a,
                observed=variant_a_successes,
            )
            likelihood_b = pm.Binomial(
                "likelihood_b",
                n=variant_b_trials,
                p=prior_b,
                observed=variant_b_successes,
            )
            
            print(f"Running {'sequential' if sequential else 'non-sequential'} Bayesian A/B test")

            if sequential:
                # Burn-in and thinning parameters for MCMC
                burn_in = 100  # Ignore the first 100 samples for model stabilization
                thinning = 5  # Only keep every 5th sample to reduce autocorrelation
                for i in range(burn_in, num_samples + 1, thinning):
                    trace = pm.sample(1, return_inferencedata=True, tune=0, target_accept=0.95)
                    posterior_prob = (
                        (trace.posterior["prior_b"] > trace.posterior["prior_a"])
                        .mean()
                        .item()
                    )
                    if posterior_prob > stopping_threshold:
                        print(
                            f"Stopping early at sample {i} with posterior probability {posterior_prob:.2f}"
                        )
                        break
            else:
                # Sample from the posterior distribution
                trace = pm.sample(
                    num_samples, 
                    return_inferencedata=True, 
                    target_accept=0.95, 
                    tune=1000  # Increase the number of tuning steps
                )

        # Calculate the uplift based on the chosen method
        self.uplift_method = uplift_method
        self.uplift_dist = calculate_uplift(trace, uplift_method)

        # Display the results
        self.plots = display_results(trace, self.uplift_dist, uplift_method)