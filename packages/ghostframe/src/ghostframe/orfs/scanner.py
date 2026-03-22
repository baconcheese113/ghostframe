"""6-frame ORF scanning engine.

Finds all maximal open reading frames (ATG to stop codon) across all 6 reading
frames of a DNA sequence. Frames 1-3 scan the forward strand at offsets 0/1/2.
Frames 4-6 scan the reverse complement at offsets 0/1/2.

An ORF is maximal: it starts at ATG and extends to the first in-frame stop codon
(TAA, TAG, TGA). The stop codon IS included in the output. ORFs shorter than
min_length bases are excluded.
"""

from ghostframe.models import ORF


def find_orfs(sequence: str, min_length: int = 50) -> list[ORF]:
    """Find all ORFs across all 6 reading frames.

    Args:
        sequence: DNA string (will be uppercased internally).
        min_length: Minimum ORF length in bases. Default is 50.

    Returns:
        List of ORF objects ordered by frame (1-6) then by position.

    Hints:
        - Uppercase the input sequence.
        - Frames 1-3 scan the forward strand at offsets 0, 1, 2.
        - Frames 4-6 scan the reverse complement at offsets 0, 1, 2.
        - Use reverse_complement() to get the reverse strand.
        - Delegate each frame to find_orfs_in_frame().
        - Results must be ordered by frame number (1-6), then by position.
    """
    raise NotImplementedError("find_orfs not yet implemented")


def find_orfs_in_frame(
    sequence: str,
    frame: int,
    min_length: int,
    original_seq_len: int | None = None,
) -> list[ORF]:
    """Find all maximal ORFs in a single reading frame.

    This is the inner loop of the scanner. It walks triplets from the frame
    offset, finds ATG start codons, and reads until the first in-frame stop.

    Args:
        sequence: DNA string (already forward or reverse-complemented).
        frame: Frame number (1-6). Frames 1-3 are forward, 4-6 are reverse.
        min_length: Minimum ORF length in bases.
        original_seq_len: Length of the original (non-complemented) sequence.
            Required for computing reverse-frame positions. If None, uses
            len(sequence).

    Returns:
        List of ORF objects for this frame, ordered by position.

    Hints:
        - The frame offset is (frame - 1) % 3.
        - Walk the sequence in steps of 3 starting from the offset.
        - When you find ATG, scan forward (in triplets) for a stop codon.
        - An ORF is maximal: first ATG to first in-frame stop. If multiple ATGs
          precede the same stop, the ORF starts at the first ATG.
        - The stop codon IS included in the ORF length and DNA.
        - If no stop codon is found before the sequence ends, it's not a valid ORF.
        - After finding a stop, continue scanning from after the stop codon.
        - Use _compute_position() for the reported position.
        - Only include ORFs with length >= min_length.
    """
    raise NotImplementedError("find_orfs_in_frame not yet implemented")


def _compute_position(  # type: ignore
    orf_start_idx: int,
    is_reverse: bool,
    original_seq_len: int,
) -> int:
    """Compute the reported position for an ORF.

    Forward frames: POS = 1-based index (orf_start_idx + 1).
    Reverse frames: POS = -(orf_start_idx + 1), representing position from
    the right end of the original sequence (rightmost base is -1).
    """
    raise NotImplementedError("_compute_position not yet implemented")
