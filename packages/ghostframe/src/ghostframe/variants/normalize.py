"""Coordinate normalization and allele handling.

Standardizes variant coordinates and allele representations for consistent
downstream processing across different input formats.

Pipeline position: variants.filters → [variants.normalize] → seqfetch → ...
"""

from ghostframe.models import NormalizedVariant, Variant


def normalize(variant: Variant) -> NormalizedVariant:
    """Normalize a variant's coordinates and alleles.

    Args:
        variant: Raw Variant record.

    Returns:
        NormalizedVariant with standardized coordinates and alleles.
    """
    raise NotImplementedError("Coordinate normalization not yet implemented")
