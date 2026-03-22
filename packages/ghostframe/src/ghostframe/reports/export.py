"""Report export in JSON and TSV formats.

Serializes analysis results into structured output files for
downstream consumption or visualization.

Pipeline position: reclassify + mhc + evidence → ranking → [reports.export] → user
"""

from pathlib import Path

from ghostframe.models import ScoredCandidate
from ghostframe.ranking import ranker


def to_json(results: object, path: Path) -> None:
    """Export analysis results as JSON.

    Args:
        results: Analysis results object.
        path: Output file path.
    """
    raise NotImplementedError("JSON export not yet implemented")


def to_tsv(candidates: list[ScoredCandidate], path: Path) -> None:
    """Export ranked candidates as a TSV file.

    Args:
        candidates: Ranked ScoredCandidate list (from ranking.ranker.rank()).
        path: Output file path.

    TSV columns (per peptide candidate):
        variant_id, frame, effect_type, peptide_seq, allele, affinity_nm,
        percentile_rank, domain_accession, domain_name, evidence_tier,
        synmicdb_score, score
    """
    ranker.to_tsv(candidates, path)
