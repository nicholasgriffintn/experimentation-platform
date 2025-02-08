import numpy as np


def holm_correction(p_values):
    """
    Apply Holm correction to p-values.

    Parameters
    ----------
    p_values : np.array
        Array of p-values from multiple tests.

    Returns
    -------
    corrected_pvalues : np.array
        Holm-corrected p-values.
    """
    sorted_p = np.argsort(p_values)
    ranked_pvalues = np.empty_like(p_values)
    ranked_pvalues[sorted_p] = np.arange(len(p_values), 0, -1)
    corrected_pvalues = p_values * ranked_pvalues
    return np.minimum.accumulate(np.minimum(corrected_pvalues, 1.0))
