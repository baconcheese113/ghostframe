"""MHCflurry adapter.

Wraps the MHCflurry open-source MHC-I binding predictor.

Pipeline position: peptides → [mhc.mhcflurry] → reports
"""

import importlib.resources
import shlex
import sys
import types

# mhcflurry 2.1.5 compatibility shims for Python 3.13 / modern uv environments:
# 1. `pipes` module was removed in Python 3.13
if "pipes" not in sys.modules:
    _pipes_shim = types.ModuleType("pipes")
    _pipes_shim.quote = shlex.quote  # type: ignore[attr-defined]
    sys.modules["pipes"] = _pipes_shim

# 2. `pkg_resources` is no longer a top-level module in setuptools 71+
if "pkg_resources" not in sys.modules:
    def _resource_string(package_or_requirement: str, resource_name: str) -> bytes:
        pkg = importlib.resources.files(package_or_requirement)
        return pkg.joinpath(resource_name).read_bytes()

    _pkg_shim = types.ModuleType("pkg_resources")
    _pkg_shim.resource_string = _resource_string  # type: ignore[attr-defined]
    sys.modules["pkg_resources"] = _pkg_shim

from mhcflurry import Class1PresentationPredictor  # type: ignore[import]

from ghostframe.mhc.base import MHCPredictor
from ghostframe.models import BindingPrediction, Peptide

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

        df = predictor.predict(alleles=alleles, peptides=sequences)

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
