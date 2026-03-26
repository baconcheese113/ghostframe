"""Candidate ranking for neoantigen prioritization.

Sorts pre-scored candidates by descending score and provides TSV export.
"""

import io
from pathlib import Path

from ghostframe.models import ScoredCandidate


def rank(candidates: list[ScoredCandidate]) -> list[ScoredCandidate]:
    """Sort candidates by descending priority score.

    Args:
        candidates: Pre-scored candidates (from scorer.score()).

    Returns:
        New list sorted descending by score. The input list is not modified.
    """
    return sorted(candidates, key=lambda c: c.score, reverse=True)


TSV_HEADER = (
    "variant_id\tframe\teffect_type\tpeptide_seq\tallele\t"
    "affinity_nm\tpercentile_rank\tdomain_accession\tdomain_name\t"
    "evidence_tier\tsynmicdb_score\tscore"
)


def to_tsv(candidates: list[ScoredCandidate], path: Path) -> None:
    """Export ranked candidates as a TSV file.

    Args:
        candidates: Ranked candidates (pass through rank() first for sorted output).
        path: Output file path.

    TSV columns:
        variant_id       — "<frame>:<pos>" from the ORF
        frame            — reading frame (1-6)
        effect_type      — reclassified effect (e.g. "Missense")
        peptide_seq      — peptide sequence from the best binding prediction
        allele           — HLA allele from the best binding prediction
        affinity_nm      — IC50 nM (lower = stronger binder)
        percentile_rank  — MHCflurry presentation percentile (0-100)
        domain_accession — Pfam accession of first domain hit, or ""
        domain_name      — Pfam name of first domain hit, or ""
        evidence_tier    — 1 (scan-only), 2 (OpenProt), or 3 (SynMICdb)
        synmicdb_score   — SynMICdb score if tier 3, else ""
        score            — aggregate priority score in [0, 1]
    """
    buf = io.StringIO()
    buf.write(TSV_HEADER + "\n")
    for c in candidates:
        orf = c.effect.orf
        variant_id = f"{orf.frame}:{orf.pos}"
        frame = str(orf.frame)
        effect_type = c.effect.new_class

        peptide_seq = c.binding.peptide.sequence if c.binding is not None else ""
        allele = c.binding.allele if c.binding is not None else ""
        affinity_nm = str(c.binding.affinity) if c.binding is not None else ""
        percentile_rank = str(c.binding.rank) if c.binding is not None else ""

        first_domain = c.domain_hits[0] if c.domain_hits else None
        domain_accession = first_domain.accession if first_domain is not None else ""
        domain_name = first_domain.name if first_domain is not None else ""

        tier = c.evidence.tier if c.evidence is not None else 1
        synmicdb_score = ""
        if c.evidence is not None and c.evidence.synmicdb is not None:
            raw = c.evidence.synmicdb.score
            synmicdb_score = str(raw) if raw is not None else ""

        buf.write(
            "\t".join(
                [
                    variant_id,
                    frame,
                    effect_type,
                    peptide_seq,
                    allele,
                    affinity_nm,
                    percentile_rank,
                    domain_accession,
                    domain_name,
                    str(tier),
                    synmicdb_score,
                    str(c.score),
                ]
            )
            + "\n"
        )
    path.write_text(buf.getvalue(), encoding="utf-8")
