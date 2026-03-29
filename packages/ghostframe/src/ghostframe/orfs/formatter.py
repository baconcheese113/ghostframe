"""ORF output formatting per the professor's assignment spec.

Output format:
    >original_header | FRAME = N POS = P LEN = L
    ATG ATA AAA GGA GTA ACC TGT GAA AAA GAT GCA ATC TAT CGT ACT
    CGC ACT TTC CCT GGT TCT GGT CGC TCC CAT GGC AGC ACA GGC TGC
    ...

Rules:
    - Space between each codon (3 bases)
    - No more than 15 codons per line
    - Header includes original description, frame, position, and length
"""

from ghostframe.models import ORF, FastaRecord

CODONS_PER_LINE = 15

# Author name: Joshua Green
def format_orf(record: FastaRecord, orf: ORF) -> str:
    """Format a single ORF in the assignment's FASTA-style output.

    Args:
        record: The source FASTA record (for the header).
        orf: The ORF to format.

    Returns:
        Formatted string including header line and codon-spaced sequence lines.

    Hints:
        - Header format: >original_description | FRAME = N POS = P LEN = L
        - Split the ORF DNA into codons (groups of 3 bases).
        - Separate codons with a single space.
        - No more than CODONS_PER_LINE (15) codons per line.
        - The last line may have fewer than 15 codons.
    """
    header = f">{record.description} | FRAME = {orf.frame} POS = {orf.pos} LEN = {orf.length}"
# split the ORF DNA into codons and format lines
    codons = [orf.dna[i : i + 3] for i in range(0, len(orf.dna), 3)]
    sequence_lines = [
        " ".join(codons[i : i + CODONS_PER_LINE]) for i in range(0, len(codons), CODONS_PER_LINE)
    ]

    return "\n".join([header, *sequence_lines])

# Author name: Joshua Green
def format_all_orfs(record: FastaRecord, orfs: list[ORF]) -> str:
    """Format all ORFs for a single FASTA record.

    Args:
        record: The source FASTA record.
        orfs: List of ORFs found in this record.

    Returns:
        Formatted string with all ORFs, separated by newlines.
        Returns empty string if orfs is empty.

    Hints:
        - Delegate each ORF to format_orf().
        - Join results with newlines.
        - Return "" for an empty list.
    """
    if not orfs:
        return ""
# format each ORF and join with newlines
    return "\n".join(format_orf(record, orf) for orf in orfs)
