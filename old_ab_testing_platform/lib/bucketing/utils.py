import hashlib


def bucket_user(user_id, bucket_count=100):
    """
    Assign a user to a bucket based on a hashed value of their user_id.

    Parameters
    ----------
    user_id : str or int
        The unique identifier for a user.

    bucket_count : int, default=100
        The total number of buckets (this determines the granularity of bucketing).

    Returns
    -------
    int
        A bucket number between 0 and bucket_count-1.
    """
    hashed_value = int(hashlib.sha256(str(user_id).encode("utf-8")).hexdigest(), 16)
    return hashed_value % bucket_count


def assign_to_group(user_id, group_buckets):
    """
    Assign a user to a group based on their bucket.

    Parameters
    ----------
    user_id : str or int
        The unique identifier for a user.

    group_buckets : dict
        A dictionary where keys are group names and values are ranges of buckets assigned to each group.

    Returns
    -------
    str
        The group name based on the user's bucket assignment.
    """
    user_bucket = bucket_user(user_id)
    for group, bucket_range in group_buckets.items():
        if user_bucket in bucket_range:
            return group
    raise ValueError("User not assigned to a valid group.")
