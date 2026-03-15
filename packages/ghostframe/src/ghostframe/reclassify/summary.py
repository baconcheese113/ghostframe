"""Reclassification summary and aggregation.

Aggregates per-variant reclassification results into summary statistics
and Sankey diagram data for visualization.

Pipeline position: reclassify.engine → [reclassify.summary] → reports
"""

from ghostframe.models import FrameEffect, ReclassifySummary


def aggregate(effects: list[FrameEffect]) -> ReclassifySummary:
    """Aggregate reclassification effects into summary statistics.

    Args:
        effects: List of FrameEffect results from the reclassification engine.

    Returns:
        ReclassifySummary with counts by effect type and Sankey flow data.
    """
    raise NotImplementedError("Reclassification summary not yet implemented")
