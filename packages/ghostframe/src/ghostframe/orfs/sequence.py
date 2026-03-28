"""DNA sequence utilities — reverse complement, codon table, translation.

These are the foundational operations that the ORF scanner depends on.
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
    # Conversion of the sequence to uppercase
    seq = seq.upper()

    # Utilize the translation table and define the complement
    comp = seq.translate(_COMPLEMENT)

    # Reverse the complement
    rev_comp = comp[::-1]

    return rev_comp

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
        if codon in STOP_CODONS:
          protein_chars.append("*")
        else:
          aa = CODON_TABLE.get(codon, "X")
          protein_chars.append(aa)

    return "".join(protein_chars)
