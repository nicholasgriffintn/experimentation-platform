import numpy as np
import pandas as pd

from .bonferroni import bonferroni_correction
from .benjamini_hochberg import benjamini_hochberg_correction
from .holm import holm_correction
from .statsmodels import statsmodels_corrections


class MultipleTestingCorrection:
    """
    When you perform multiple hypothesis tests, the probability of
    obtaining false positives (incorrectly rejecting a true null hypothesis)
    increases.

    This class provides methods to adjust p-values to control for this increased
    risk, ensuring more reliable and accurate results.

    Methods Supported:
    ------------------
    - Bonferroni Correction
        - Controls the family-wise error rate by adjusting p-values to be more stringent.
    - Benjamini-Hochberg (FDR) Correction
        - Controls the false discovery rate, balancing the discovery of true positives and limiting false positives.
    - Holm Correction
        - A step-down method that is less conservative than Bonferroni but still controls the family-wise error rate.
    - Statsmodels Corrections
        - Utilizes the statsmodels library to apply various correction methods.

    Example Usage:

    # Example p-values from multiple A/B tests
    p_values = [0.03, 0.02, 0.07, 0.04, 0.01, 0.05, 0.15]

    # Initialize the correction class
    correction = MultipleTestingCorrection(p_values)

    # Apply Bonferroni correction
    print("Bonferroni Corrected P-Values:")
    print(correction.bonferroni_correction())

    # Apply Benjamini-Hochberg correction
    print("\nBenjamini-Hochberg (FDR) Corrected P-Values:")
    print(correction.benjamini_hochberg_correction())

    # Apply Holm correction
    print("\nHolm Corrected P-Values:")
    print(correction.holm_correction())

    # Using statsmodels built-in corrections for summary
    print("\nSummary of Corrected P-Values using 'fdr_bh':")
    print(correction.summary(method='fdr_bh'))
    """

    def __init__(self, p_values):
        """
        Initialize the correction class with a list of p-values.

        Parameters
        ----------
        p_values : list or np.array
            List or array of p-values from multiple tests.
        """
        self.p_values = np.array(p_values)

    def bonferroni_correction(self):
        """
        Apply Bonferroni correction to p-values.

        Returns
        -------
        corrected_pvalues : np.array
            Bonferroni-corrected p-values.
        """
        return bonferroni_correction(self.p_values)

    def benjamini_hochberg_correction(self):
        """
        Apply Benjamini-Hochberg (FDR) correction to p-values.

        Returns
        -------
        corrected_pvalues : np.array
            FDR-corrected p-values using the Benjamini-Hochberg method.
        """
        return benjamini_hochberg_correction(self.p_values)

    def holm_correction(self):
        """
        Apply Holm correction to p-values.

        Returns
        -------
        corrected_pvalues : np.array
            Holm-corrected p-values.
        """
        return holm_correction(self.p_values)

    def apply_statsmodels_corrections(self, method="fdr_bh"):
        """
        Use statsmodels to apply various p-value correction methods.

        Parameters
        ----------
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
        return statsmodels_corrections(self.p_values, method)

    def summary(self, method="fdr_bh"):
        """
        Display a summary of the original p-values and their corrected values.

        Parameters
        ----------
        method : str, default='fdr_bh'
            The correction method to apply for the summary.

        Returns
        -------
        pd.DataFrame
            DataFrame summarizing original and corrected p-values.
        """
        original_pvalues = self.p_values
        corrected_pvalues = self.apply_statsmodels_corrections(method=method)
        summary_df = pd.DataFrame(
            {
                "Original P-Value": original_pvalues,
                "Corrected P-Value": corrected_pvalues,
            }
        )
        return summary_df
