"""Codon-level effect comparison.

Compares a reference codon to an alternate codon to determine
whether the amino acid change is synonymous, missense, or nonsense.

Pipeline position: reclassify.engine calls [reclassify.codon_effect]
"""

from ghostframe.models import CodonEffect


def compare(ref_codon: str, alt_codon: str) -> CodonEffect:
    """Compare two codons and classify the effect.

    Args:
        ref_codon: Reference codon (3 DNA characters).
        alt_codon: Alternate codon (3 DNA characters).

    Returns:
        CodonEffect with ref/alt amino acids and effect type.
    """
    raise NotImplementedError("Codon effect comparison not yet implemented")
