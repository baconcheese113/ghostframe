"""Tests for MHCflurry binding prediction adapter."""

import pytest

from ghostframe.mhc.mhcflurry import MHCflurryPredictor, _DEFAULT_ALLELES
from ghostframe.models import BindingPrediction, Peptide

# GILGFVFTL — well-characterized HLA-A*02:01 strong binder (influenza M1 58-66)
_STRONG_BINDER = "GILGFVFTL"
_WEAK_BINDER = "AAAAAAAAAA"  # poly-Ala 10-mer, expected weak binder


def _make_peptide(seq: str) -> Peptide:
    return Peptide(sequence=seq, start=0, k=len(seq))


@pytest.mark.slow
class TestMHCflurryPredictor:
    def test_returns_binding_predictions(self) -> None:
        predictor = MHCflurryPredictor()
        peptides = [_make_peptide(_STRONG_BINDER)]
        results = predictor.predict(peptides, alleles=["HLA-A*02:01"])
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], BindingPrediction)

    def test_one_result_per_peptide(self) -> None:
        # Class1PresentationPredictor selects the best allele per peptide —
        # one result per peptide regardless of how many alleles are supplied.
        predictor = MHCflurryPredictor()
        peptides = [_make_peptide(_STRONG_BINDER), _make_peptide(_WEAK_BINDER)]
        alleles = ["HLA-A*02:01", "HLA-B*07:02"]
        results = predictor.predict(peptides, alleles=alleles)
        assert len(results) == len(peptides)

    def test_known_strong_binder(self) -> None:
        predictor = MHCflurryPredictor()
        peptides = [_make_peptide(_STRONG_BINDER)]
        results = predictor.predict(peptides, alleles=["HLA-A*02:01"])
        assert results[0].affinity < 500  # IC50 < 500 nM = strong binder

    def test_default_allele(self) -> None:
        predictor = MHCflurryPredictor()
        peptides = [_make_peptide(_STRONG_BINDER)]
        results = predictor.predict(peptides, alleles=[])
        assert all(r.allele == _DEFAULT_ALLELES[0] for r in results)

    def test_affinity_and_rank_populated(self) -> None:
        predictor = MHCflurryPredictor()
        peptides = [_make_peptide(_STRONG_BINDER)]
        results = predictor.predict(peptides, alleles=["HLA-A*02:01"])
        for r in results:
            assert r.affinity > 0
            assert 0 <= r.rank <= 100

    def test_peptide_reference_preserved(self) -> None:
        predictor = MHCflurryPredictor()
        original = _make_peptide(_STRONG_BINDER)
        results = predictor.predict([original], alleles=["HLA-A*02:01"])
        assert results[0].peptide is original
