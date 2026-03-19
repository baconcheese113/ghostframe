"""Variant classification filtering.

Filters variants by their annotation classification (e.g., keep only "Silent"
variants for reclassification analysis).

Pipeline position: variants.maf → [variants.filters] → variants.normalize → ...
"""

from ghostframe.models import Variant


def keep_silent(variants: list[Variant]) -> list[Variant]:
    """Filter to keep only variants classified as Silent.

    Args:
        variants: List of Variant records.

    Returns:
        Filtered list containing only Silent variants.
    """
    return [v for v in variants if v.classification == "Silent"]
