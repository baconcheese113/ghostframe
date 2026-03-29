"""FASTA file parser.

Handles multi-sequence files, sequences split across lines,
whitespace within sequences, and mixed case normalization.
"""

from pathlib import Path

from ghostframe.models import FastaRecord

# Author name: Joshua Green 
def parse_file(path: Path | str) -> list[FastaRecord]:
    """Parse a FASTA file from a filesystem path.

    Args:
        path: Path to a FASTA file.

    Returns:
        List of FastaRecord objects with sequences normalized to uppercase.

    Hints:
        - Read the file and delegate to parse_text().
    """
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        text = f.read()

    return parse_text(text)

# Author name: Joshua Green
def parse_text(text: str) -> list[FastaRecord]:
    """Parse FASTA from a raw string.

    Args:
        text: Raw FASTA-formatted string.

    Returns:
        List of FastaRecord objects with sequences normalized to uppercase.

    Hints:
        - Lines starting with '>' are headers; everything else is sequence data.
        - The record ID is the first whitespace-delimited token of the header.
        - The description is the full header (everything after '>').
        - Sequence lines may be split across multiple lines — concatenate them.
        - Strip whitespace from sequence lines and normalize to uppercase.
        - Empty lines between sequences should be ignored.
        - Text with no '>' headers should return an empty list.
    """
    records: list[FastaRecord] = []
    header: str | None = None
    sequence_lines: list[str] = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue  # skip empty lines

        if line.startswith(">"):
            # Save previous record if exists
            if header is not None:
                #concatenate sequence lines, remove spaces, and uppercase
                sequence = "".join(sequence_lines).replace(" ", "").upper()
                record_id = header.split()[0]
                records.append(FastaRecord(id=record_id, description=header, sequence=sequence))

            # Start new record
            header = line[1:].strip()
            sequence_lines = []
        else:
            # Accumulate sequence lines
            sequence_lines.append(line)

    # Add last record
    if header is not None:
        sequence = "".join(sequence_lines).replace(" ", "").upper()
        record_id = header.split()[0]
        records.append(FastaRecord(id=record_id, description=header, sequence=sequence))

    return records
