"""Sliding-window peptide generation.

Generates all k-mer peptides spanning a mutant position in a protein
sequence, for use in MHC binding prediction.

Pipeline position: reclassify → orfs.sequence.translate → [peptides.generator] → mhc
"""

from ghostframe.models import Peptide


def sliding_kmers(
    protein: str,
    mut_pos: int,
    k_range: tuple[int, int] = (8, 11),
) -> list[Peptide]:
    """Generate all k-mer peptides spanning a mutant position.

    Args:
        protein: Full protein sequence.
        mut_pos: 0-based position of the mutation in the protein.
        k_range: Tuple of (min_k, max_k) for peptide lengths.

    Returns:
        List of Peptide objects spanning the mutant position.
    """
    raise NotImplementedError("Peptide generation not yet implemented")
