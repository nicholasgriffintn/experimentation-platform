from .lib.bucketing import UserBucketingABTest
from .lib.corrections import MultipleTestingCorrection


def run_experiment(
    user_data, group_buckets, method, alpha=0.05, prior_successes=30, prior_trials=100, sequential=False, stopping_threshold=None
):
    """
    Run an A/B test based on the provided user data.
    """
    if method not in ["frequentist", "bayesian"]:
        return {
            "error": "Invalid method. Please choose either 'frequentist' or 'bayesian'."
        }

    if method == "frequentist":
        ab_test = UserBucketingABTest(method="frequentist", alpha=alpha, sequential=sequential, stopping_threshold=stopping_threshold)
    else:
        ab_test = UserBucketingABTest(
            method="bayesian",
            prior_successes=prior_successes,
            prior_trials=prior_trials,
            sequential=sequential,
            stopping_threshold=stopping_threshold,
        )

    result = ab_test.run_experiment(user_data, group_buckets)

    if result is None:
        return {"error": "Error running the experiment."}

    results = {"method": method, "results": result}

    if method == "frequentist":
        p_values = []
        for test_group, res in result.items():
            p_values.append(res["pvalue"])

        # Apply multiple testing correction if there are multiple p-values
        if len(p_values) > 1:
            correction_method = "fdr_bh"  # Default correction method
            correction = MultipleTestingCorrection(p_values)
            corrected_p_values = correction.apply_statsmodels_corrections(
                method=correction_method
            )
            results["correction_method"] = correction_method
            results["corrected_p_values"] = dict(zip(result.keys(), corrected_p_values))

    return results
