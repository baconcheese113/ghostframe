"""Report export in JSON and TSV formats.

Serializes analysis results into structured output files for
downstream consumption or visualization.

Pipeline position: reclassify + mhc + evidence → [reports.export] → user
"""

import csv
import dataclasses
import json
from pathlib import Path

from ghostframe.models import FastLaneResult


def to_json(results: FastLaneResult, path: Path) -> None:
    """Export analysis results as JSON.

    Args:
        results: FastLaneResult from the fast lane pipeline.
        path: Output file path.
    """
    path.write_text(json.dumps(dataclasses.asdict(results), indent=2))


def to_tsv(results: FastLaneResult, path: Path) -> None:
    """Export reclassified variants as TSV.

    Args:
        results: FastLaneResult from the fast lane pipeline.
        path: Output file path.
    """
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["old_class", "new_class", "ref_aa", "alt_aa", "frame"])
        for effect in results.reclassified_variants:
            writer.writerow(
                [
                    effect.old_class,
                    effect.new_class,
                    effect.ref_aa,
                    effect.alt_aa,
                    effect.orf.frame,
                ]
            )
