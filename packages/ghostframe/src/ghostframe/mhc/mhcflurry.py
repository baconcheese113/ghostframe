"""MHCflurry adapter.

Wraps the MHCflurry open-source MHC-I binding predictor.

Pipeline position: peptides → [mhc.mhcflurry] → reports
"""

import numpy as np
import torch
from mhcflurry import Class1PresentationPredictor  # type: ignore[import-untyped]

from ghostframe.mhc.base import MHCPredictor
from ghostframe.models import BindingPrediction, Peptide

# mhcflurry 2.2.0rc1 passes read-only NumPy arrays to torch.from_numpy(),
# which requires writable arrays (known RC bug). Patch at import time.
_orig_from_numpy = torch.from_numpy  # type: ignore[assignment]


def _from_numpy_writable(array: np.ndarray) -> torch.Tensor:  # type: ignore[type-arg]
    if not array.flags.writeable:
        array = array.copy()
    return _orig_from_numpy(array)  # type: ignore[return-value]


torch.from_numpy = _from_numpy_writable  # type: ignore[assignment]

_DEFAULT_ALLELES = ["HLA-A*02:01"]


class MHCflurryPredictor(MHCPredictor):
    """MHCflurry-based MHC-I binding predictor."""

    _predictor: Class1PresentationPredictor | None = None

    @classmethod
    def _load(cls) -> Class1PresentationPredictor:
        if cls._predictor is None:
            cls._predictor = Class1PresentationPredictor.load()
        return cls._predictor

    def predict(
        self,
        peptides: list[Peptide],
        alleles: list[str],
    ) -> list[BindingPrediction]:
        """Predict MHC-I binding affinity using MHCflurry.

        Args:
            peptides: List of Peptide objects to score.
            alleles: List of HLA allele names (e.g., ["HLA-A*02:01"]).
                     Defaults to ["HLA-A*02:01"] if empty.

        Returns:
            List of BindingPrediction results, one per (peptide, allele) pair.
        """
        if not alleles:
            alleles = _DEFAULT_ALLELES

        predictor = self._load()
        sequences = [p.sequence for p in peptides]

        df = predictor.predict(alleles=alleles, peptides=sequences)  # type: ignore[union-attr]

        # Class1PresentationPredictor returns one row per peptide with the
        # best-binding allele from the supplied list (best_allele column).
        seq_to_peptide = {p.sequence: p for p in peptides}
        return [
            BindingPrediction(
                peptide=seq_to_peptide[row["peptide"]],
                allele=row["best_allele"],
                affinity=row["affinity"],
                rank=row["presentation_percentile"],
            )
            for _, row in df.iterrows()
        ]
