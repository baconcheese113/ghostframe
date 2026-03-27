"""Shared genetics constants and sequence utilities.

Provides the standard genetic code, complement tables, and sequence
operations used across GhostFrame modules.
"""

from ghostframe.orfs.sequence import CODON_TABLE, STOP_CODONS

__all__ = ["CODON_TABLE", "STOP_CODONS", "reverse_complement", "translate"]

_COMPLEMENT = str.maketrans("ACGT", "TGCA")


def reverse_complement(seq: str) -> str:
    """Return the reverse complement of a DNA sequence.

    Args:
        seq: DNA string (A, C, G, T characters).

    Returns:
        Reverse complement DNA string.
    """
    return seq.upper().translate(_COMPLEMENT)[::-1]


def translate(dna: str) -> str:
    """Translate a DNA sequence to a protein sequence.

    Args:
        dna: DNA string whose length must be a multiple of 3.

    Returns:
        Protein string (stop codons represented as '*').

    Raises:
        ValueError: If the DNA length is not a multiple of 3.
    """
    dna = dna.upper()
    if len(dna) % 3 != 0:
        raise ValueError(f"DNA length {len(dna)} is not a multiple of 3")
    return "".join(CODON_TABLE.get(dna[i : i + 3], "X") for i in range(0, len(dna), 3))
