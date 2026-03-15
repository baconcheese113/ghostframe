"""MHCflurry adapter.

Wraps the MHCflurry open-source MHC-I binding predictor.
Future dependency: mhcflurry (pip install mhcflurry)

Pipeline position: peptides → [mhc.mhcflurry] → reports
"""

from ghostframe.mhc.base import MHCPredictor
from ghostframe.models import BindingPrediction, Peptide


class MHCflurryPredictor(MHCPredictor):
    """MHCflurry-based MHC-I binding predictor."""

    def predict(
        self,
        peptides: list[Peptide],
        alleles: list[str],
    ) -> list[BindingPrediction]:
        """Predict binding using MHCflurry.

        Args:
            peptides: List of Peptide objects to score.
            alleles: List of HLA allele names.

        Returns:
            List of BindingPrediction results.
        """
        raise NotImplementedError("MHCflurry adapter not yet implemented")
