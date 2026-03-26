"""Unit tests for pipeline.deep_lane.

All external calls (MHCflurry, HMMER, OpenProt, SynMICdb, ClinVar) are
mocked so the suite runs fast with no network or model dependencies.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ghostframe.models import (
    ORF,
    BindingPrediction,
    DeepLaneResult,
    DomainHit,
    EvidenceLookupResult,
    FastLaneResult,
    FrameEffect,
    NormalizedVariant,
    Peptide,
    ReclassifySummary,
    ScoredCandidate,
    SynMICdbHit,
)
from ghostframe.pipeline import deep_lane
from ghostframe.reports import export

# --- Helpers ---

# 30-nt ORF: Met + 9xAla + stop -> protein "MAAAAAAAAA"
_DNA_30 = "ATG" + "GCC" * 9 + "TAA"

_BINDING_TARGET = "ghostframe.pipeline.deep_lane.MHCflurryPredictor"
_HMMER_TARGET = "ghostframe.pipeline.deep_lane.hmmer.scan"
_OPENPROT_TARGET = "ghostframe.pipeline.deep_lane.openprot.lookup"
_SYNMICDB_TARGET = "ghostframe.pipeline.deep_lane.synmicdb.lookup"
_CLINVAR_TARGET = "ghostframe.pipeline.deep_lane.clinvar.lookup"


def _make_orf() -> ORF:
    return ORF(frame=1, pos=1, length=30, dna=_DNA_30)


def _make_variant() -> NormalizedVariant:
    return NormalizedVariant(
        chrom="17",
        pos=7675994,
        ref="G",
        alt="T",
        classification="Silent",
        gene="TP53",
    )


def _make_effect(
    codon_pos: int | None = None,
    with_variant: bool = False,
) -> FrameEffect:
    return FrameEffect(
        orf=_make_orf(),
        old_class="Silent",
        new_class="Missense",
        ref_aa="A",
        alt_aa="V",
        codon_pos=codon_pos,
        variant=_make_variant() if with_variant else None,
    )


def _make_fast_result(effects: list[FrameEffect]) -> FastLaneResult:
    return FastLaneResult(
        summary=ReclassifySummary(),
        sankey_data=[],
        reclassified_variants=effects,
    )


def _make_binding() -> BindingPrediction:
    return BindingPrediction(
        peptide=Peptide(sequence="GILGFVFTL", start=0, k=9),
        allele="HLA-A*02:01",
        affinity=120.0,
        rank=1.5,
    )


def _make_domain_hit() -> DomainHit:
    return DomainHit(accession="PF00071", name="Ras", start=1, end=9, score=42.0)


def _make_mock_predictor(binding: BindingPrediction | None = None) -> MagicMock:
    bp = binding or _make_binding()
    mock_cls: MagicMock = MagicMock()
    mock_cls.return_value.predict.return_value = [bp]
    return mock_cls


# --- Tests ---


@patch(_CLINVAR_TARGET, return_value=None)
@patch(_SYNMICDB_TARGET, return_value=None)
@patch(_OPENPROT_TARGET, return_value=None)
@patch(_HMMER_TARGET, return_value=[])
def test_run_empty_effects(
    _mock_hmmer: MagicMock,
    _mock_op: MagicMock,
    _mock_syn: MagicMock,
    _mock_cv: MagicMock,
) -> None:
    """Empty reclassified_variants -> empty DeepLaneResult."""
    with patch(_BINDING_TARGET, _make_mock_predictor()):
        result = deep_lane.run(_make_fast_result([]))

    assert isinstance(result, DeepLaneResult)
    assert result.peptides == []
    assert result.binding_predictions == []
    assert result.ranked_candidates == []
    assert result.evidence is None


@patch(_CLINVAR_TARGET, return_value=None)
@patch(_SYNMICDB_TARGET, return_value=None)
@patch(_OPENPROT_TARGET, return_value=None)
@patch(_HMMER_TARGET, return_value=[])
def test_run_produces_ranked_candidates(
    _mock_hmmer: MagicMock,
    _mock_op: MagicMock,
    _mock_syn: MagicMock,
    _mock_cv: MagicMock,
) -> None:
    """Single effect produces one ranked ScoredCandidate."""
    binding = _make_binding()
    with patch(_BINDING_TARGET, _make_mock_predictor(binding)):
        result = deep_lane.run(_make_fast_result([_make_effect(codon_pos=1)]))

    assert len(result.ranked_candidates) == 1
    cand = result.ranked_candidates[0]
    assert isinstance(cand, ScoredCandidate)
    assert cand.binding == binding
    assert 0.0 <= cand.score <= 1.0


@patch(_CLINVAR_TARGET, return_value=None)
@patch(_SYNMICDB_TARGET, return_value=None)
@patch(_OPENPROT_TARGET, return_value=None)
@patch(_HMMER_TARGET, return_value=[])
def test_run_none_variant_skips_evidence_lookups(
    mock_hmmer: MagicMock,
    mock_op: MagicMock,
    mock_syn: MagicMock,
    mock_cv: MagicMock,
) -> None:
    """When effect.variant is None, evidence lookups are not called."""
    with patch(_BINDING_TARGET, _make_mock_predictor()):
        deep_lane.run(_make_fast_result([_make_effect(codon_pos=1, with_variant=False)]))

    mock_hmmer.assert_called_once()
    mock_op.assert_not_called()
    mock_syn.assert_not_called()
    mock_cv.assert_not_called()


@patch(_CLINVAR_TARGET, return_value=None)
@patch(_SYNMICDB_TARGET, return_value=None)
@patch(_OPENPROT_TARGET, return_value=None)
@patch(_HMMER_TARGET, return_value=[])
def test_run_with_variant_calls_evidence_lookups(
    _mock_hmmer: MagicMock,
    mock_op: MagicMock,
    mock_syn: MagicMock,
    mock_cv: MagicMock,
) -> None:
    """When effect.variant is set, all three evidence lookups are called."""
    with patch(_BINDING_TARGET, _make_mock_predictor()):
        deep_lane.run(_make_fast_result([_make_effect(codon_pos=1, with_variant=True)]))

    mock_op.assert_called_once()
    mock_syn.assert_called_once()
    mock_cv.assert_called_once()


@patch(_CLINVAR_TARGET, return_value=None)
@patch(_SYNMICDB_TARGET, return_value=None)
@patch(_OPENPROT_TARGET, return_value=None)
@patch(_HMMER_TARGET, return_value=[])
def test_run_no_codon_pos_falls_back_to_all_kmers(
    _mock_hmmer: MagicMock,
    _mock_op: MagicMock,
    _mock_syn: MagicMock,
    _mock_cv: MagicMock,
) -> None:
    """When codon_pos is None, peptides are still generated (all k-mer fallback)."""
    with patch(_BINDING_TARGET, _make_mock_predictor()):
        result = deep_lane.run(_make_fast_result([_make_effect(codon_pos=None)]))

    # Protein from _DNA_30 is "MAAAAAAAAA" (10 AA). 8-10mers fit.
    assert len(result.peptides) > 0


@patch(_CLINVAR_TARGET, return_value=None)
@patch(_SYNMICDB_TARGET)
@patch(_OPENPROT_TARGET, return_value=None)
@patch(_HMMER_TARGET, return_value=[])
def test_run_evidence_tier_escalates_with_synmicdb(
    _mock_hmmer: MagicMock,
    _mock_op: MagicMock,
    mock_syn: MagicMock,
    _mock_cv: MagicMock,
) -> None:
    """A SynMICdb hit pushes evidence tier to 3."""
    synmicdb_hit = SynMICdbHit(
        gene_name="TP53",
        transcript_id="NM_000546",
        mutation_id="TP53:c.375G>T",
        mutation_nt="c.375G>T",
        mutation_aa="p.Ala125Val",
        genome_position="17:7675994",
        chrom="17",
        start=7675994,
        end=7675994,
        strand="-",
        frequency=0.01,
        avg_mutation_load=None,
        alternative_events=None,
        snp=None,
        conservation=None,
        structure_change_score=None,
        structure_change_significance=None,
        score=0.9,
    )
    mock_syn.return_value = synmicdb_hit

    with patch(_BINDING_TARGET, _make_mock_predictor()):
        result = deep_lane.run(_make_fast_result([_make_effect(codon_pos=1, with_variant=True)]))

    assert result.ranked_candidates[0].evidence is not None
    assert result.ranked_candidates[0].evidence.tier == 3


@patch(_CLINVAR_TARGET, return_value=None)
@patch(_SYNMICDB_TARGET, return_value=None)
@patch(_OPENPROT_TARGET, return_value=None)
@patch(_HMMER_TARGET, return_value=[])
def test_run_multiple_effects_all_ranked(
    _mock_hmmer: MagicMock,
    _mock_op: MagicMock,
    _mock_syn: MagicMock,
    _mock_cv: MagicMock,
) -> None:
    """Multiple effects each produce a ScoredCandidate sorted descending by score."""
    effects = [_make_effect(codon_pos=1), _make_effect(codon_pos=2)]
    with patch(_BINDING_TARGET, _make_mock_predictor()):
        result = deep_lane.run(_make_fast_result(effects))

    assert len(result.ranked_candidates) == 2
    scores = [c.score for c in result.ranked_candidates]
    assert scores == sorted(scores, reverse=True)


# --- to_json tests ---


def _make_deep_lane_result() -> DeepLaneResult:
    binding = _make_binding()
    effect = _make_effect(codon_pos=1)
    candidate = ScoredCandidate(
        effect=effect,
        binding=binding,
        domain_hits=[_make_domain_hit()],
        evidence=EvidenceLookupResult(tier=2),
        score=0.75,
    )
    return DeepLaneResult(
        peptides=[binding.peptide],
        binding_predictions=[binding],
        evidence=EvidenceLookupResult(tier=2),
        domain_hits=[_make_domain_hit()],
        ranked_candidates=[candidate],
    )


def test_to_json_creates_valid_json(tmp_path: Path) -> None:
    """to_json writes a file that is valid JSON."""
    out = tmp_path / "result.json"
    export.to_json(_make_deep_lane_result(), out)
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_to_json_contains_ranked_candidates(tmp_path: Path) -> None:
    """JSON output includes 'ranked_candidates' key."""
    out = tmp_path / "result.json"
    export.to_json(_make_deep_lane_result(), out)
    data = json.loads(out.read_text())
    assert "ranked_candidates" in data
    assert len(data["ranked_candidates"]) == 1


def test_to_json_score_value_preserved(tmp_path: Path) -> None:
    """Score value is correctly serialized to JSON."""
    out = tmp_path / "result.json"
    export.to_json(_make_deep_lane_result(), out)
    data = json.loads(out.read_text())
    assert abs(data["ranked_candidates"][0]["score"] - 0.75) < 1e-9


# --- Integration test ---


@pytest.mark.integration
@pytest.mark.slow
def test_run_integration_hpv16_orf() -> None:
    """End-to-end deep lane run with real MHCflurry + HMMER APIs."""
    dna = "ATG" + "GCC" * 9 + "TAA"
    orf = ORF(frame=1, pos=1, length=len(dna), dna=dna)
    effect = FrameEffect(
        orf=orf,
        old_class="Silent",
        new_class="Missense",
        ref_aa="A",
        alt_aa="V",
        codon_pos=3,
    )
    fast_result = FastLaneResult(
        summary=ReclassifySummary(),
        sankey_data=[],
        reclassified_variants=[effect],
    )
    result = deep_lane.run(fast_result, hla_alleles=["HLA-A*02:01"])
    assert isinstance(result, DeepLaneResult)
    assert len(result.ranked_candidates) == 1
    assert result.ranked_candidates[0].score >= 0.0
