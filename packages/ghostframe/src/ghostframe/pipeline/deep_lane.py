"""Deep lane pipeline — background, per-variant enrichment.

peptide generation → MHC binding prediction → domain annotation →
external evidence linking → candidate scoring → ranking.

Triggered per-variant on user click in the dashboard, or called directly
for batch analysis.
"""

from ghostframe.domain import hmmer
from ghostframe.evidence import clinvar, openprot, synmicdb
from ghostframe.genetics import translate
from ghostframe.mhc.mhcflurry import MHCflurryPredictor
from ghostframe.models import (
    DeepLaneResult,
    EvidenceLookupResult,
    FastLaneResult,
    Peptide,
    ScoredCandidate,
)
from ghostframe.peptides.generator import sliding_kmers
from ghostframe.ranking import ranker, scorer

_DEFAULT_ALLELES = ["HLA-A*02:01"]


def run(
    fast_result: FastLaneResult,
    hla_alleles: list[str] | None = None,
) -> DeepLaneResult:
    """Run deep analysis for each reclassified variant in a FastLaneResult.

    Args:
        fast_result: Output of the fast lane, containing reclassified variants.
        hla_alleles: HLA alleles for MHC-I binding prediction. Defaults to
            ["HLA-A*02:01"] when None.

    Returns:
        DeepLaneResult with ranked candidates, all peptides, binding
        predictions, domain hits, and aggregated evidence for the top
        candidate.
    """
    alleles = hla_alleles or _DEFAULT_ALLELES
    predictor = MHCflurryPredictor()

    all_peptides: list[Peptide] = []
    candidates: list[ScoredCandidate] = []

    for effect in fast_result.reclassified_variants:
        protein = translate(effect.orf.dna)

        # Peptides: target mutation position if known, else generate all k-mers
        if effect.codon_pos is not None:
            peptides = sliding_kmers(protein, effect.codon_pos)
        else:
            peptides = _all_kmers(protein)

        all_peptides.extend(peptides)

        # MHC binding
        binding_preds = predictor.predict(peptides, alleles) if peptides else []
        best_binding = min(binding_preds, key=lambda b: b.rank) if binding_preds else None

        # Domain annotation
        domain_hits = hmmer.scan(protein)

        # Evidence (requires source variant attached to the effect)
        if effect.variant is not None:
            openprot_hit = openprot.lookup(effect.orf, effect.variant.gene)
            synmicdb_hit = synmicdb.lookup(effect.variant)
            clinvar_hit = clinvar.lookup(effect.variant)
        else:
            openprot_hit = None
            synmicdb_hit = None
            clinvar_hit = None

        tier = 3 if synmicdb_hit else (2 if openprot_hit else 1)
        evidence = EvidenceLookupResult(
            openprot=openprot_hit,
            synmicdb=synmicdb_hit,
            clinvar=clinvar_hit,
            tier=tier,
        )

        s = scorer.score(effect, best_binding, domain_hits, evidence)
        candidates.append(
            ScoredCandidate(
                effect=effect,
                binding=best_binding,
                domain_hits=domain_hits,
                evidence=evidence,
                score=s,
            )
        )

    ranked = ranker.rank(candidates)

    return DeepLaneResult(
        peptides=all_peptides,
        binding_predictions=[c.binding for c in ranked if c.binding is not None],
        evidence=ranked[0].evidence if ranked else None,
        domain_hits=[h for c in ranked for h in c.domain_hits],
        ranked_candidates=ranked,
    )


def _all_kmers(protein: str, k_min: int = 8, k_max: int = 11) -> list[Peptide]:
    """Generate all unique k-mers from a protein sequence.

    Used as a fallback when the mutation position (codon_pos) is unknown.
    Skips peptides containing stop codons (*) or unknown amino acids (X).
    """
    seen: set[str] = set()
    peptides: list[Peptide] = []
    for k in range(k_min, k_max + 1):
        for i in range(len(protein) - k + 1):
            seq = protein[i : i + k]
            if "*" in seq or "X" in seq:
                continue
            if seq not in seen:
                seen.add(seq)
                peptides.append(Peptide(sequence=seq, start=i, k=k))
    return peptides
