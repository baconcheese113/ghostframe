"""DNA sequence utilities — reverse complement, codon table, translation.

These are the foundational operations that the ORF scanner depends on.
Re-exported from ghostframe.genetics so group members' imports are unaffected.
"""

from ghostframe.genetics import CODON_TABLE, STOP_CODONS, reverse_complement, translate

__all__ = ["CODON_TABLE", "STOP_CODONS", "reverse_complement", "translate"]
