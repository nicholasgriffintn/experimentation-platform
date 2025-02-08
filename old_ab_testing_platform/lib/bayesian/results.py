import numpy as np
import arviz as az
import matplotlib.pyplot as plt
import tempfile

from .plotting import plot_uplift_distribution


def display_results(trace, uplift_dist, uplift_method):
    """Display the results of the Bayesian A/B test."""
    uplift_percent_above_0 = np.mean(uplift_dist >= 0)

    # Print summary of results
    summary = (
        "\nBayesian A/B Test Summary\n==========================\n"
        f"Evaluation Metric: {uplift_method.capitalize()} Uplift\n"
        f"Uplift above threshold: {uplift_percent_above_0 * 100:.2f}% of simulations\n"
    )
    print(summary)

    # Plot the posterior distributions and uplift
    uplift_image = plot_uplift_distribution(uplift_dist, uplift_method)

    # Use ArviZ to summarize the posterior distributions
    posterior_summary = az.summary(trace)
    print("\nPosterior Distributions\n=======================")
    print(posterior_summary)

    # Plot posterior distributions
    az.plot_posterior(trace)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_file.name, format="png")
    plt.close()

    return {
        "summary": summary,
        "posterior_summary": posterior_summary,
        "uplift_image": uplift_image,
        "posterior_image": temp_file.name,
    }
