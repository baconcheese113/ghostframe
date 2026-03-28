"""Codon-level effect comparison.

Compares a reference codon to an alternate codon to determine
whether the amino acid change is synonymous, missense, or nonsense.

Pipeline position: reclassify.engine calls [reclassify.codon_effect]
"""

from ghostframe.models import CodonEffect
from ghostframe.orfs.sequence import CODON_TABLE


def compare(ref_codon: str, alt_codon: str) -> CodonEffect:
    """Compare two codons and classify the effect.

    Args:
        ref_codon: Reference codon (3 DNA characters).
        alt_codon: Alternate codon (3 DNA characters).

    Returns:
        CodonEffect with ref/alt amino acids and effect type.
    """
    ref_aa = CODON_TABLE.get(ref_codon.upper(), "X")
    alt_aa = CODON_TABLE.get(alt_codon.upper(), "X")

    if alt_aa == "*" and ref_aa != "*":
        effect_type = "stop_gain"
    elif ref_aa == "*" and alt_aa != "*":
        effect_type = "stop_loss"
    elif ref_aa == alt_aa:
        effect_type = "synonymous"
    elif ref_aa == "M" and alt_aa != "M":
        effect_type = "start_loss"
    else:
        effect_type = "missense"

    return CodonEffect(ref_aa=ref_aa, alt_aa=alt_aa, effect_type=effect_type)
