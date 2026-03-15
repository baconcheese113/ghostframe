"""Core reclassification logic.

For each variant overlapping an ORF, determines whether the variant
changes the encoded amino acid in that frame.

Pipeline position: orfs → [reclassify.engine] → peptides
"""

from ghostframe.models import ORF, FrameEffect, NormalizedVariant


def reclassify(variant: NormalizedVariant, orfs: list[ORF]) -> list[FrameEffect]:
    """Reclassify a variant's effect across all overlapping ORFs.

    Args:
        variant: Normalized variant with standardized coordinates.
        orfs: List of ORFs that overlap the variant position.

    Returns:
        List of FrameEffect objects, one per overlapping ORF.
    """
    raise NotImplementedError("Variant reclassification not yet implemented")
