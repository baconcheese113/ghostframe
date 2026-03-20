"""6-frame ORF scanning engine.

Finds all maximal open reading frames (ATG to stop codon) across all 6 reading
frames of a DNA sequence. Frames 1-3 scan the forward strand at offsets 0/1/2.
Frames 4-6 scan the reverse complement at offsets 0/1/2.

An ORF is maximal: it starts at ATG and extends to the first in-frame stop codon
(TAA, TAG, TGA). The stop codon IS included in the output. ORFs shorter than
min_length bases are excluded.
"""

from ghostframe.models import ORF
from ghostframe.orfs.sequence import STOP_CODONS, reverse_complement


def find_orfs(sequence: str, min_length: int = 50) -> list[ORF]:
    """Find all ORFs across all 6 reading frames.

    Args:
        sequence: DNA string (will be uppercased internally).
        min_length: Minimum ORF length in bases. Default is 50.

    Returns:
        List of ORF objects ordered by frame (1-6) then by position.
    """
    sequence = sequence.upper()
    rc = reverse_complement(sequence)
    orfs: list[ORF] = []
    for frame in range(1, 4):
        orfs.extend(find_orfs_in_frame(sequence, frame, min_length))
    for frame in range(4, 7):
        orfs.extend(find_orfs_in_frame(rc, frame, min_length, original_seq_len=len(sequence)))
    orfs.sort(key=lambda o: (o.frame, o.pos))
    return orfs


def find_orfs_in_frame(
    sequence: str,
    frame: int,
    min_length: int,
    original_seq_len: int | None = None,
) -> list[ORF]:
    """Find all maximal ORFs in a single reading frame.

    Args:
        sequence: DNA string (already forward or reverse-complemented).
        frame: Frame number (1-6). Frames 1-3 are forward, 4-6 are reverse.
        min_length: Minimum ORF length in bases.
        original_seq_len: Length of the original (non-complemented) sequence.
            Required for computing reverse-frame positions. If None, uses
            len(sequence).

    Returns:
        List of ORF objects for this frame, ordered by position.
    """
    if original_seq_len is None:
        original_seq_len = len(sequence)
    is_reverse = frame >= 4
    offset = (frame - 1) % 3
    orfs: list[ORF] = []
    orf_start: int | None = None
    i = offset
    while i + 3 <= len(sequence):
        codon = sequence[i : i + 3].upper()
        if codon == "ATG" and orf_start is None:
            orf_start = i
        elif codon in STOP_CODONS and orf_start is not None:
            orf_end = i + 3
            orf_dna = sequence[orf_start:orf_end]
            orf_length = orf_end - orf_start
            if orf_length >= min_length:
                pos = _compute_position(orf_start, is_reverse, original_seq_len)
                orfs.append(ORF(frame=frame, pos=pos, length=orf_length, dna=orf_dna))
            orf_start = None
        i += 3
    return orfs


def _compute_position(
    orf_start_idx: int,
    is_reverse: bool,
    original_seq_len: int,
) -> int:
    """Compute the reported position for an ORF.

    Forward frames: POS = 1-based index (orf_start_idx + 1).
    Reverse frames: POS = -(orf_start_idx + 1), representing position from
    the right end of the original sequence (rightmost base is -1).
    """
    if is_reverse:
        return -(orf_start_idx + 1)
    return orf_start_idx + 1
