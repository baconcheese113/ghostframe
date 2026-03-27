"""Unit tests for ranking.scorer."""

from ghostframe.models import (
    ORF,
    BindingPrediction,
    DomainHit,
    EvidenceLookupResult,
    FrameEffect,
    Peptide,
)
from ghostframe.ranking import scorer

# --- Helpers ---


def _make_orf() -> ORF:
    return ORF(frame=1, pos=1, length=30, dna="ATG" * 10)


def _make_effect() -> FrameEffect:
    return FrameEffect(
        orf=_make_orf(), old_class="Silent", new_class="Missense", ref_aa="A", alt_aa="V"
    )


def _make_binding(rank: float, affinity: float = 100.0) -> BindingPrediction:
    return BindingPrediction(
        peptide=Peptide(sequence="GILGFVFTL", start=0, k=9),
        allele="HLA-A*02:01",
        affinity=affinity,
        rank=rank,
    )


def _make_domain_hit() -> DomainHit:
    return DomainHit(accession="PF00071", name="Ras", start=5, end=39, score=42.0)


def _make_evidence(tier: int) -> EvidenceLookupResult:
    return EvidenceLookupResult(tier=tier)


# --- Tests ---


def test_score_perfect_candidate() -> None:
    """rank=0, tier=3, domain hit → max score 1.0."""
    s = scorer.score(
        effect=_make_effect(),
        binding=_make_binding(rank=0.0),
        domain_hits=[_make_domain_hit()],
        evidence=_make_evidence(tier=3),
    )
    assert s == 1.0


def test_score_worst_candidate() -> None:
    """rank=100, tier=1, no domains → min score 0.0."""
    s = scorer.score(
        effect=_make_effect(),
        binding=_make_binding(rank=100.0),
        domain_hits=[],
        evidence=_make_evidence(tier=1),
    )
    assert s == 0.0


def test_score_none_binding() -> None:
    """binding=None → MHC term is 0; score is still a valid float."""
    s = scorer.score(
        effect=_make_effect(),
        binding=None,
        domain_hits=[],
        evidence=_make_evidence(tier=1),
    )
    assert s == 0.0


def test_score_none_evidence() -> None:
    """evidence=None → treated as tier 1; MHC and domain terms still apply."""
    s = scorer.score(
        effect=_make_effect(),
        binding=_make_binding(rank=0.0),
        domain_hits=[_make_domain_hit()],
        evidence=None,
    )
    # 0.5 * 1.0 + 0.3 * 0.0 + 0.2 = 0.7
    assert abs(s - 0.7) < 1e-9


def test_score_tier2_no_domain() -> None:
    """tier=2 evidence, no domain, rank=0 → 0.5 + 0.15 + 0.0 = 0.65."""
    s = scorer.score(
        effect=_make_effect(),
        binding=_make_binding(rank=0.0),
        domain_hits=[],
        evidence=_make_evidence(tier=2),
    )
    assert abs(s - 0.65) < 1e-9


def test_acceptance_criteria_comparison() -> None:
    """Acceptance criteria: IC50<500 + tier3 + domain > IC50>2000 + tier1 + no domain."""
    # MHCflurry rank ~1-5 for IC50 < 500 nM strong binder; use rank=2 as representative
    strong = scorer.score(
        effect=_make_effect(),
        binding=_make_binding(rank=2.0, affinity=300.0),
        domain_hits=[_make_domain_hit()],
        evidence=_make_evidence(tier=3),
    )
    # Weak binder: IC50 > 2000 nM corresponds to high rank; use rank=80
    weak = scorer.score(
        effect=_make_effect(),
        binding=_make_binding(rank=80.0, affinity=2500.0),
        domain_hits=[],
        evidence=_make_evidence(tier=1),
    )
    assert strong > weak


def test_score_range_all_tiers_and_ranks() -> None:
    """All combinations of tier/rank/domain produce scores in [0, 1]."""
    for tier in (1, 2, 3):
        for rank in (0.0, 50.0, 100.0):
            for has_domain in (True, False):
                domain_hits = [_make_domain_hit()] if has_domain else []
                s = scorer.score(
                    effect=_make_effect(),
                    binding=_make_binding(rank=rank),
                    domain_hits=domain_hits,
                    evidence=_make_evidence(tier=tier),
                )
                assert 0.0 <= s <= 1.0, f"Score {s} out of range for tier={tier} rank={rank}"
