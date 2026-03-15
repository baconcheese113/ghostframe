"""Report export in JSON and TSV formats.

Serializes analysis results into structured output files for
downstream consumption or visualization.

Pipeline position: reclassify + mhc + evidence → [reports.export] → user
"""

from pathlib import Path


def to_json(results: object, path: Path) -> None:
    """Export analysis results as JSON.

    Args:
        results: Analysis results object.
        path: Output file path.
    """
    raise NotImplementedError("JSON export not yet implemented")


def to_tsv(results: object, path: Path) -> None:
    """Export analysis results as TSV.

    Args:
        results: Analysis results object.
        path: Output file path.
    """
    raise NotImplementedError("TSV export not yet implemented")
