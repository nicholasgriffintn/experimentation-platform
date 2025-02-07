def validate_hypothesis(alt_hypothesis, alpha):
    """Validate the hypothesis input and alpha level."""
    valid_hypotheses = ["one_tailed", "two_tailed"]
    if alt_hypothesis not in valid_hypotheses:
        raise ValueError(
            f"Invalid hypothesis type: {alt_hypothesis}. Choose from {valid_hypotheses}."
        )
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha should be between 0 and 1, but got {alpha}.")
