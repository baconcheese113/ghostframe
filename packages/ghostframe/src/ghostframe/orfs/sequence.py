"""DNA sequence utilities — reverse complement, codon table, translation.

These are the foundational operations that the ORF scanner depends on.
Re-exported from ghostframe.genetics so group members' imports are unaffected.
"""

from ghostframe.genetics import CODON_TABLE

__all__ = ["CODON_TABLE", "STOP_CODONS", "reverse_complement", "translate"]

STOP_CODONS = {"TAA", "TAG", "TGA"}

_COMPLEMENT = str.maketrans("ACGT", "TGCA")


def reverse_complement(seq: str) -> str:
    """Return the reverse complement of a DNA sequence.

    Input is normalized to uppercase before complementing.

    Args:
        seq: DNA string (A, C, G, T characters).

    Returns:
        Reverse complement DNA string.

    Hints:
        - A pairs with T, C pairs with G.
        - The _COMPLEMENT translation table and str.translate() may be useful.
        - Don't forget to reverse the string after complementing.
    """
    seq = seq.upper()
    return seq.translate(_COMPLEMENT)[::-1]


def translate(dna: str) -> str:
    """Translate a DNA sequence to a protein sequence using the standard genetic code.

    Args:
        dna: DNA string whose length must be a multiple of 3.

    Returns:
        Protein string (stop codons represented as '*').

    Raises:
        ValueError: If the DNA length is not a multiple of 3.

    Hints:
        - Normalize input to uppercase first.
        - Raise ValueError if len(dna) is not divisible by 3.
        - Walk the string in steps of 3, look up each codon in CODON_TABLE.
        - Use 'X' for any codon not found in the table.
    """
    dna = dna.upper()
    if len(dna) % 3 != 0:
        raise ValueError("DNA length is not a multiple of 3")

    protein_chars: list[str] = []
    for i in range(0, len(dna), 3):
        codon = dna[i : i + 3]
        aa = CODON_TABLE.get(codon, "X")
        protein_chars.append(aa)

    return "".join(protein_chars)
