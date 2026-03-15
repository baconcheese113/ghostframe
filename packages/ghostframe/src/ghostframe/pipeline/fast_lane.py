"""Fast lane pipeline — synchronous, seconds-scale analysis.

intake → filter → coordinate normalization → sequence fetch →
6-frame ORF scan → reclassification → cohort summary stats.

Powers the dashboard immediately.
"""

from pathlib import Path
from typing import Literal

from ghostframe.models import FastLaneResult


def run(
    source: Path,
    source_type: Literal["maf", "fasta"],
    min_orf_length: int = 50,
) -> FastLaneResult:
    """Run the synchronous fast analysis pipeline.

    Args:
        source: Path to input file (MAF or FASTA).
        source_type: Type of input file.
        min_orf_length: Minimum ORF length for scanning.

    Returns:
        FastLaneResult with summary statistics, Sankey data, and
        per-variant reclassification results.
    """
    raise NotImplementedError("Fast lane pipeline not yet implemented")
