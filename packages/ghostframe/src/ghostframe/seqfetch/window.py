"""Genomic window extraction around a variant.

Computes a flanking region around a variant position and retrieves the
reference sequence for ORF scanning.

Pipeline position: variants.normalize → [seqfetch.window] → orfs
"""

from pathlib import Path

from ghostframe.models import GenomicWindow, NormalizedVariant


def extract(
    variant: NormalizedVariant,
    ref_path: Path,
    flank: int = 500,
) -> GenomicWindow:
    """Extract a genomic window around a variant for ORF scanning.

    Args:
        variant: Normalized variant with standardized coordinates.
        ref_path: Path to the reference FASTA.
        flank: Number of bases to include on each side of the variant.

    Returns:
        GenomicWindow containing the reference sequence.
    """
    raise NotImplementedError("Genomic window extraction not yet implemented")
