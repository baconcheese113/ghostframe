"""Genomic window extraction around a variant.

Computes a flanking region around a variant position and slices the
reference sequence for ORF scanning.

Pipeline position: variants.normalize → [seqfetch.window] → orfs
"""

from ghostframe.models import GenomicWindow, NormalizedVariant


def extract(
    variant: NormalizedVariant,
    sequence: str,
    flank: int = 500,
) -> GenomicWindow:
    """Extract a genomic window around a variant from a pre-fetched sequence.

    Args:
        variant: Normalized variant with standardized coordinates.
        sequence: Full reference sequence string for the chromosome/region.
        flank: Number of bases to include on each side of the variant.

    Returns:
        GenomicWindow with start/end bounds and the sliced sequence.
    """
    # variant.pos is 1-based; convert to 0-based
    start = max(0, variant.pos - 1 - flank)
    end = variant.pos - 1 + len(variant.ref) + flank

    return GenomicWindow(
        chrom=variant.chrom,
        start=start,
        end=end,
        sequence=sequence[start:end].upper(),
    )
