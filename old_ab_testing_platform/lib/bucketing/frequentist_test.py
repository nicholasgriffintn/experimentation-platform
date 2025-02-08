from ..frequentist import FrequentistABTest


def run_frequentist_test(
    group_results, alpha, sequential=False, stopping_threshold=None
):
    """
    Run Frequentist A/B testing.

    Parameters
    ----------
    group_results : dict
        A dictionary with group names as keys and dictionaries with 'success' and 'trials' as values.

    alpha : float
        Significance level for Frequentist A/B testing.

    sequential : bool, optional
        Whether to use sequential testing.

    stopping_threshold : float, optional
        The threshold for stopping the experiment early if sequential testing is used.

    Returns
    -------
    dict
        A dictionary with the test statistic and p-value.
    """
    control_group = "control"
    test_groups = [group for group in group_results.keys() if group != control_group]

    results = {}
    for test_group in test_groups:
        control_success = group_results[control_group]["success"]
        control_trials = group_results[control_group]["trials"]
        test_success = group_results[test_group]["success"]
        test_trials = group_results[test_group]["trials"]

        exp = FrequentistABTest(alpha=alpha, alt_hypothesis="two_tailed")
        exp_results = exp.run_experiment(
            control_success,
            control_trials,
            test_success,
            test_trials,
            sequential=sequential,
            stopping_threshold=stopping_threshold,
        )

        results[test_group] = exp_results

    return results
