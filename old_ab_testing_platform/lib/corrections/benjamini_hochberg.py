import numpy as np


def benjamini_hochberg_correction(p_values):
    """
    Apply Benjamini-Hochberg (FDR) correction to p-values.

    Parameters
    ----------
    p_values : np.array
        Array of p-values from multiple tests.

    Returns
    -------
    corrected_pvalues : np.array
        FDR-corrected p-values using the Benjamini-Hochberg method.
    """
    sorted_p = np.argsort(p_values)
    ranked_pvalues = np.empty_like(p_values)
    ranked_pvalues[sorted_p] = np.arange(1, len(p_values) + 1)
    corrected_pvalues = p_values * len(p_values) / ranked_pvalues
    return np.minimum.accumulate(np.minimum(corrected_pvalues, 1.0))
