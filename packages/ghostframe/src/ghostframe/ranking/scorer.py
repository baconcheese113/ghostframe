"""Candidate scoring for neoantigen prioritization.

Combines three signals into a single priority score in [0, 1]:
  - MHC binding percentile rank (lower rank = stronger predicted binder)
  - External evidence tier (OpenProt / SynMICdb confirmation)
  - Pfam domain presence (known functional domain in the ORF)

Weights are module-level constants and can be tuned without changing the formula.
"""

from ghostframe.models import (
    BindingPrediction,
    DomainHit,
    EvidenceLookupResult,
    FrameEffect,
)

# Scoring weights — must sum to 1.0
_W_MHC: float = 0.5
_W_EVIDENCE: float = 0.3
_W_DOMAIN: float = 0.2


def score(
    effect: FrameEffect,
    binding: BindingPrediction | None,
    domain_hits: list[DomainHit],
    evidence: EvidenceLookupResult | None,
) -> float:
    """Score a reclassified variant candidate.

    Args:
        effect: The FrameEffect describing the reclassified variant.
        binding: Best MHC binding prediction for peptides from this ORF,
            or None if no prediction was made.
        domain_hits: Pfam domain hits in the translated ORF (may be empty).
        evidence: Aggregated external evidence, or None if not looked up.

    Returns:
        Float in [0, 1]; higher = higher priority neoantigen candidate.

        Score components:
          - MHC:      0.5 * (1 - percentile_rank / 100)
                      → 0.5 when rank=0 (best binder); 0.0 when rank=100 or no binding
          - Evidence: 0.3 * (tier - 1) / 2
                      → 0.0 at tier 1 (scan-only); 0.3 at tier 3 (SynMICdb-scored)
          - Domain:   0.2 if any domain_hits, else 0.0
    """
    mhc_term = _W_MHC * (1.0 - binding.rank / 100.0) if binding is not None else 0.0
    tier = evidence.tier if evidence is not None else 1
    evidence_term = _W_EVIDENCE * (tier - 1) / 2.0
    domain_term = _W_DOMAIN if domain_hits else 0.0
    return mhc_term + evidence_term + domain_term
