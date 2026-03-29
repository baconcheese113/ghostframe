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

from ghostframe.models import ORF, FastaRecord  # Import required models

CODONS_PER_LINE = 15  # Max codons per line

# Author name: Joshua Green
def format_orf(record: FastaRecord, orf: ORF) -> str:
    
    # Build header line with ORF details
    header = f">{record.description} | FRAME = {orf.frame} POS = {orf.pos} LEN = {orf.length}"

    # Split DNA sequence into codons (3 bases each)
    codons = [orf.dna[i:i+3] for i in range(0, len(orf.dna), 3)]

    # Group codons into lines of up to 15 codons
    sequence_lines = [
        " ".join(codons[i:i+CODONS_PER_LINE])
        for i in range(0, len(codons), CODONS_PER_LINE)
    ]

    # Combine header and sequence lines
    return "\n".join([header, *sequence_lines])


# Author name: Joshua Green
def format_all_orfs(record: FastaRecord, orfs: list[ORF]) -> str:
    
    # Return empty string if no ORFs
    if not orfs:
        return ""

    # Format each ORF and join with newlines
    return "\n".join(format_orf(record, orf) for orf in orfs)
