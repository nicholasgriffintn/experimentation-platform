import json


def validate_input_data(numerator, denominator):
    """
    Validates input data for consistency in A/B testing.

    Parameters
    ----------
    numerator : int
        Number of successful events (e.g., clicks).
    denominator : int
        Total number of events (e.g., impressions).

    Raises
    ------
    ValueError
        If any of the validation checks fail (e.g., negative values, non-integer types).
    """
    if not isinstance(numerator, int) or not isinstance(denominator, int):
        raise TypeError("Both 'numerator' and 'denominator' must be integers.")
    if numerator < 0:
        raise ValueError(
            "The number of successful events (numerator) cannot be negative."
        )
    if denominator <= 0:
        raise ValueError(
            "The total number of events (denominator) must be greater than zero."
        )
    if numerator > denominator:
        raise ValueError(
            f"The number of successful events ({numerator}) cannot exceed the total events ({denominator})."
        )


def validate_probability_parameter(parameter):
    """
    Validates a parameter to ensure it is within the probability range [0, 1].

    Parameters
    ----------
    parameter : float
        Probability value (e.g., significance level or error rate).

    Raises
    ------
    ValueError
        If the parameter is not within the valid probability range [0, 1].
    """
    if not isinstance(parameter, (float, int)):
        raise TypeError("The parameter must be a float or an integer.")
    if not (0 <= parameter <= 1):
        raise ValueError("The parameter must be between 0 and 1 (inclusive).")


def is_t_test_required(trials_a, trials_b):
    """
    Determines whether a t-test is required based on sample size.

    Parameters
    ----------
    trials_a : int
        Total number of trials in group A.
    trials_b : int
        Total number of trials in group B.

    Returns
    -------
    bool
        True if a t-test is required (sample size is small), False otherwise.

    Notes
    -----
    A t-test is typically used when the combined sample size is less than 30.
    """
    if not isinstance(trials_a, int) or not isinstance(trials_b, int):
        raise TypeError("Both 'trials_a' and 'trials_b' must be integers.")

    return (trials_a + trials_b) < 30


def load_user_data(file_path: str):
    """
    Load user data from a JSON file.

    Parameters
    ----------
    file_path : str
        Path to the JSON file containing user data.

    Returns
    -------
    list
        A list of user data dictionaries.
    """
    with open(file_path, "r") as f:
        user_data = json.load(f)
    return user_data


def parse_group_buckets(group_buckets: str):
    """
    Parse the group buckets string into a dictionary.
    """
    group_buckets_dict = {}
    for group in group_buckets.split(","):
        name, range_str = group.split(":")
        start, end = map(int, range_str.split("-"))
        group_buckets_dict[name] = range(start, end)
    return group_buckets_dict
