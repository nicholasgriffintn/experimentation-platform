def calculate_uplift(trace, uplift_method):
    """Calculate the uplift distribution based on the selected method."""
    posterior_a = trace.posterior["prior_a"].values.flatten()
    posterior_b = trace.posterior["prior_b"].values.flatten()

    if uplift_method == "percent":
        uplift_dist = (posterior_b - posterior_a) / posterior_a
    elif uplift_method == "ratio":
        uplift_dist = posterior_b / posterior_a
    elif uplift_method == "difference":
        uplift_dist = posterior_b - posterior_a
    else:
        raise ValueError(
            f"Invalid uplift method: {uplift_method}. Use 'percent', 'ratio', or 'difference'."
        )

    return uplift_dist
