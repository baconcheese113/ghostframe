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
    counts_by_type: dict[str, int] = {}
    sankey_counts: dict[tuple[str, str], int] = {}

    for effect in effects:
        counts_by_type[effect.new_class] = counts_by_type.get(effect.new_class, 0) + 1
        key = (effect.old_class, effect.new_class)
        sankey_counts[key] = sankey_counts.get(key, 0) + 1

    sankey_data: list[dict[str, str | int]] = [
        {"from": old_class, "to": new_class, "count": count}
        for (old_class, new_class), count in sankey_counts.items()
    ]

    return ReclassifySummary(counts_by_type=counts_by_type, sankey_data=sankey_data)
