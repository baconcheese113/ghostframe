"""Abstract base class for MHC binding predictors.

Defines the interface that all MHC predictor adapters must implement.
"""

from abc import ABC, abstractmethod

from ghostframe.models import BindingPrediction, Peptide


class MHCPredictor(ABC):
    """Abstract base for MHC-I binding prediction."""

    @abstractmethod
    def predict(
        self,
        peptides: list[Peptide],
        alleles: list[str],
    ) -> list[BindingPrediction]:
        """Predict MHC binding affinity for peptides against HLA alleles.

        Args:
            peptides: List of Peptide objects to score.
            alleles: List of HLA allele names (e.g., ["HLA-A02:01"]).

        Returns:
            List of BindingPrediction results.
        """
        ...
