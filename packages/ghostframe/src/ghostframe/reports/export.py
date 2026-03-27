"""Report export in JSON and TSV formats.

Serializes analysis results into structured output files for
downstream consumption or visualization.

Pipeline position: reclassify + mhc + evidence → ranking → [reports.export] → user
"""

import dataclasses
import json
from pathlib import Path

from ghostframe.models import DeepLaneResult, ScoredCandidate
from ghostframe.ranking import ranker


def to_json(result: DeepLaneResult, path: Path) -> None:
    """Export a DeepLaneResult as a JSON file.

    Args:
        result: Deep lane analysis result.
        path: Output file path.

    The output is a JSON object with full provenance per candidate:
    peptides, binding predictions, domain hits, evidence, and ranked
    candidates with aggregate scores.
    """
    data = dataclasses.asdict(result)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


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
