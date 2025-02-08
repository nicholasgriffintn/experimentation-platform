import numpy as np


def bonferroni_correction(p_values):
    """
    Apply Bonferroni correction to p-values.

    Parameters
    ----------
    p_values : np.array
        Array of p-values from multiple tests.

    Returns
    -------
    corrected_pvalues : np.array
        Bonferroni-corrected p-values.
    """
    corrected_pvalues = np.minimum(p_values * len(p_values), 1.0)
    return corrected_pvalues
