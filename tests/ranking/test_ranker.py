"""Unit tests for ranking.ranker."""

from pathlib import Path

from ghostframe.models import (
    ORF,
    BindingPrediction,
    DomainHit,
    EvidenceLookupResult,
    FrameEffect,
    Peptide,
    ScoredCandidate,
)
from ghostframe.ranking import ranker

# --- Helpers ---


def _make_candidate(score: float) -> ScoredCandidate:
    orf = ORF(frame=1, pos=1, length=30, dna="ATG" * 10)
    effect = FrameEffect(orf=orf, old_class="Silent", new_class="Missense", ref_aa="A", alt_aa="V")
    binding = BindingPrediction(
        peptide=Peptide(sequence="GILGFVFTL", start=0, k=9),
        allele="HLA-A*02:01",
        affinity=100.0,
        rank=5.0,
    )
    return ScoredCandidate(
        effect=effect,
        binding=binding,
        domain_hits=[DomainHit(accession="PF00071", name="Ras", start=5, end=39, score=42.0)],
        evidence=EvidenceLookupResult(tier=2),
        score=score,
    )


# --- Tests ---


def test_rank_descending_order() -> None:
    candidates = [_make_candidate(0.3), _make_candidate(0.9), _make_candidate(0.6)]
    result = ranker.rank(candidates)
    scores = [c.score for c in result]
    assert scores == sorted(scores, reverse=True)


def test_rank_returns_new_list() -> None:
    candidates = [_make_candidate(0.5), _make_candidate(0.8)]
    result = ranker.rank(candidates)
    assert result is not candidates


def test_rank_does_not_mutate_input() -> None:
    original_order = [0.3, 0.9, 0.6]
    candidates = [_make_candidate(s) for s in original_order]
    ranker.rank(candidates)
    assert [c.score for c in candidates] == original_order


def test_rank_empty_list() -> None:
    assert ranker.rank([]) == []


def test_rank_single_candidate() -> None:
    c = _make_candidate(0.75)
    assert ranker.rank([c]) == [c]


def test_to_tsv_creates_file_with_score_column(tmp_path: Path) -> None:
    candidates = [_make_candidate(0.8)]
    out = tmp_path / "out.tsv"
    ranker.to_tsv(candidates, out)
    header = out.read_text(encoding="utf-8").splitlines()[0]
    assert "score" in header.split("\t")


def test_to_tsv_rows_match_candidates(tmp_path: Path) -> None:
    candidates = [_make_candidate(0.8), _make_candidate(0.4)]
    out = tmp_path / "out.tsv"
    ranker.to_tsv(candidates, out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    # header + one row per candidate
    assert len(lines) == 1 + len(candidates)


def test_to_tsv_score_value_in_row(tmp_path: Path) -> None:
    c = _make_candidate(0.75)
    out = tmp_path / "out.tsv"
    ranker.to_tsv([c], out)
    row = out.read_text(encoding="utf-8").splitlines()[1]
    cols = row.split("\t")
    header_cols = ranker.TSV_HEADER.split("\t")
    score_idx = header_cols.index("score")
    assert float(cols[score_idx]) == 0.75


def test_to_tsv_empty_list(tmp_path: Path) -> None:
    out = tmp_path / "out.tsv"
    ranker.to_tsv([], out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1  # header only


def test_to_tsv_none_binding(tmp_path: Path) -> None:
    """Candidates without a binding prediction produce empty binding columns."""
    orf = ORF(frame=2, pos=10, length=30, dna="ATG" * 10)
    effect = FrameEffect(
        orf=orf, old_class="Silent", new_class="Stop_Gained", ref_aa="Q", alt_aa="*"
    )
    c = ScoredCandidate(
        effect=effect,
        binding=None,
        domain_hits=[],
        evidence=None,
        score=0.0,
    )
    out = tmp_path / "out.tsv"
    ranker.to_tsv([c], out)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    # Should not raise; empty binding fields are fine
    row = lines[1].split("\t")
    header_cols = ranker.TSV_HEADER.split("\t")
    assert row[header_cols.index("peptide_seq")] == ""
    assert row[header_cols.index("allele")] == ""
