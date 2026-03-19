"""Shared genetics constants and sequence utilities.

Provides the standard genetic code, complement tables, and sequence
operations used across GhostFrame modules.
"""

# Standard genetic code (DNA codon -> amino acid)
CODON_TABLE: dict[str, str] = {
    "TTT": "F",
    "TTC": "F",
    "TTA": "L",
    "TTG": "L",
    "CTT": "L",
    "CTC": "L",
    "CTA": "L",
    "CTG": "L",
    "ATT": "I",
    "ATC": "I",
    "ATA": "I",
    "ATG": "M",
    "GTT": "V",
    "GTC": "V",
    "GTA": "V",
    "GTG": "V",
    "TCT": "S",
    "TCC": "S",
    "TCA": "S",
    "TCG": "S",
    "CCT": "P",
    "CCC": "P",
    "CCA": "P",
    "CCG": "P",
    "ACT": "T",
    "ACC": "T",
    "ACA": "T",
    "ACG": "T",
    "GCT": "A",
    "GCC": "A",
    "GCA": "A",
    "GCG": "A",
    "TAT": "Y",
    "TAC": "Y",
    "TAA": "*",
    "TAG": "*",
    "CAT": "H",
    "CAC": "H",
    "CAA": "Q",
    "CAG": "Q",
    "AAT": "N",
    "AAC": "N",
    "AAA": "K",
    "AAG": "K",
    "GAT": "D",
    "GAC": "D",
    "GAA": "E",
    "GAG": "E",
    "TGT": "C",
    "TGC": "C",
    "TGA": "*",
    "TGG": "W",
    "CGT": "R",
    "CGC": "R",
    "CGA": "R",
    "CGG": "R",
    "AGT": "S",
    "AGC": "S",
    "AGA": "R",
    "AGG": "R",
    "GGT": "G",
    "GGC": "G",
    "GGA": "G",
    "GGG": "G",
}

STOP_CODONS: set[str] = {"TAA", "TAG", "TGA"}

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
