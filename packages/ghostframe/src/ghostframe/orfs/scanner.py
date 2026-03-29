"""6-frame ORF scanning engine.

Finds all maximal open reading frames (ATG to stop codon) across all 6 reading
frames of a DNA sequence. Frames 1-3 scan the forward strand at offsets 0/1/2.
Frames 4-6 scan the reverse complement at offsets 0/1/2.

An ORF is maximal: it starts at ATG and extends to the first in-frame stop codon
(TAA, TAG, TGA). The stop codon IS included in the output. ORFs shorter than
min_length bases are excluded.
"""

from ghostframe.models import ORF  # Import ORF data structure
from ghostframe.orfs.sequence import STOP_CODONS, reverse_complement  # Import stop codons and reverse complement function

# Author name: Joshua Green
def find_orfs(sequence: str, min_length: int = 50) -> list[ORF]:

    sequence = sequence.upper()  # Normalize sequence to uppercase
    original_seq_len = len(sequence)  # Store original sequence length
    results: list[ORF] = []  # List to collect all ORFs

    # Scan forward strand (frames 1–3)
    for frame in range(1, 4):
        results.extend(
            find_orfs_in_frame(
                sequence=sequence,
                frame=frame,
                min_length=min_length,
                original_seq_len=original_seq_len,
            )
        )

    # Get reverse complement for reverse frames
    rev_seq = reverse_complement(sequence)

    # Scan reverse strand (frames 4–6)
    for frame in range(4, 7):
        results.extend(
            find_orfs_in_frame(
                sequence=rev_seq,
                frame=frame,
                min_length=min_length,
                original_seq_len=original_seq_len,
            )
        )

    # Sort ORFs by frame, then by position
    return sorted(results, key=lambda orf: (orf.frame, orf.pos))


# Author name: Joshua Green
def find_orfs_in_frame(
    sequence: str,
    frame: int,
    min_length: int,
    original_seq_len: int | None = None,
) -> list[ORF]:

    sequence = sequence.upper()  # Ensure sequence is uppercase

    # Use sequence length if original not provided
    if original_seq_len is None:
        original_seq_len = len(sequence)

    offset = (frame - 1) % 3  # Determine frame offset (0,1,2)
    is_reverse = frame >= 4  # Check if this is a reverse frame
    orfs: list[ORF] = []  # Store ORFs found in this frame

    i = offset  # Start scanning from frame offset

    # Loop through sequence in steps of 3 (codons)
    while i <= len(sequence) - 3:
        codon = sequence[i : i + 3]  # Get current codon

        # If not a start codon, move to next codon
        if codon != "ATG":
            i += 3
            continue

        stop_idx = None  # Initialize stop position
        j = i + 3  # Start scanning after ATG

        # Scan forward for stop codon
        while j <= len(sequence) - 3:
            next_codon = sequence[j : j + 3]
            if next_codon in STOP_CODONS:  # Check if stop codon
                stop_idx = j
                break
            j += 3

        # If no stop codon found, stop scanning
        if stop_idx is None:
            break

        # Extract ORF DNA including stop codon
        orf_dna = sequence[i : stop_idx + 3]
        orf_length = len(orf_dna)

        # Only keep ORFs that meet minimum length
        if orf_length >= min_length:
            position = _compute_position(
                orf_start_idx=i,
                is_reverse=is_reverse,
                original_seq_len=original_seq_len,
            )

            # Create ORF object and add to list
            orfs.append(
                ORF(
                    frame=frame,
                    pos=position,
                    length=orf_length,
                    dna=orf_dna,
                )
            )

        # Move index to after stop codon (continue scanning)
        i = stop_idx + 3

    return orfs  # Return ORFs found in this frame


def _compute_position(  # type: ignore
    orf_start_idx: int,
    is_reverse: bool,
    original_seq_len: int,
) -> int:

    # Forward strand: position is 1-based index
    if not is_reverse:
        return orf_start_idx + 1

    # Reverse strand: negative position from right end
    return -(orf_start_idx + 1)
