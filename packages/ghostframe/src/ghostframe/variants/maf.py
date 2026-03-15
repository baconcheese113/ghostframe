"""MAF file parser for GDC open-access mutation annotation format.

This module ingests MAF files and extracts variant records needed for
multi-frame reclassification. It is the primary data intake path for
cancer cohort analysis.

Pipeline position: INPUT → [variants.maf] → variants.filters → ...
"""

from pathlib import Path

from ghostframe.models import Variant


def parse(path: Path) -> list[Variant]:
    """Parse a GDC open-access MAF file into Variant records.

    Args:
        path: Path to a .maf file (tab-separated, GDC format).

    Returns:
        List of Variant records with chrom, pos, ref, alt, classification, gene.
    """
    raise NotImplementedError("MAF parsing not yet implemented")
