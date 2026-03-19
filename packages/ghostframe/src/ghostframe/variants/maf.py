"""MAF file parser for GDC open-access mutation annotation format.

This module ingests MAF files and extracts variant records needed for
multi-frame reclassification. It is the primary data intake path for
cancer cohort analysis.

Pipeline position: INPUT → [variants.maf] → variants.filters → ...
"""

import csv
from pathlib import Path

from ghostframe.models import Variant


def parse(path: Path) -> list[Variant]:
    """Parse a GDC open-access MAF file into Variant records.

    Args:
        path: Path to a .maf file (tab-separated, GDC format).

    Returns:
        List of Variant records with chrom, pos, ref, alt, classification, gene.
    """
    variants: list[Variant] = []
    with open(path, encoding="utf-8") as f:
        lines = (line for line in f if not line.startswith("#"))
        for row in csv.DictReader(lines, delimiter="\t"):
            variants.append(
                Variant(
                    chrom=row["Chromosome"],
                    pos=int(row["Start_Position"]),
                    ref=row["Reference_Allele"],
                    alt=row["Tumor_Seq_Allele2"],
                    classification=row["Variant_Classification"],
                    gene=row["Hugo_Symbol"],
                )
            )
    return variants
