"""Sliding-window peptide generation.

Generates all k-mer peptides spanning a mutant position in a protein
sequence, for use in MHC binding prediction.

Pipeline position: reclassify → orfs.sequence.translate → [peptides.generator] → mhc
"""

from ghostframe.models import Peptide


def sliding_kmers(
    protein: str,
    mut_pos: int,
    k_min: int = 8,
    k_max: int = 11,
) -> list[Peptide]:
    """Generate k-mer peptides that span the mutant position.

    Args:
        protein: Full protein sequence (single-letter AA codes).
        mut_pos: 0-based position of the mutated amino acid.
        k_min: Minimum peptide length (inclusive).
        k_max: Maximum peptide length (inclusive).

    Returns:
        All k-mers of lengths k_min..k_max that contain mut_pos,
        skipping any window with stop ('*') or unknown ('X') characters.
    """
    results: list[Peptide] = []
    for k in range(k_min, k_max + 1):
        # A window of size k starting at `start` contains mut_pos iff:
        #   start <= mut_pos < start + k  →  start in [mut_pos-k+1, mut_pos]
        start_lo = max(0, mut_pos - k + 1)
        start_hi = min(len(protein) - k, mut_pos)
        for start in range(start_lo, start_hi + 1):
            window = protein[start : start + k]
            if "*" in window or "X" in window:
                continue
            results.append(Peptide(sequence=window, start=start, k=k))
    return results
