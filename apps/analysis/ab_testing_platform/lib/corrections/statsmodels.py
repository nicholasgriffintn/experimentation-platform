from statsmodels.stats.multitest import multipletests


def statsmodels_corrections(p_values, method="fdr_bh"):
    """
    Use statsmodels to apply various p-value correction methods.

    Parameters
    ----------
    p_values : np.array
        Array of p-values from multiple tests.

    method : str
        The correction method to apply. Supported methods are:
        - 'bonferroni'
        - 'fdr_bh' (Benjamini-Hochberg)
        - 'holm'

    Returns
    -------
    corrected_pvalues : np.array
        Corrected p-values based on the chosen method.
    """
    _, corrected_pvalues, _, _ = multipletests(p_values, method=method)
    return corrected_pvalues
