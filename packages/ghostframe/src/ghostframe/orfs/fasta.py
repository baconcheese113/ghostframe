"""FASTA file parser.

Handles multi-sequence files, sequences split across lines,
whitespace within sequences, and mixed case normalization.
"""

from pathlib import Path  # Used to handle file paths in an OS-independent way

from ghostframe.models import FastaRecord  # Import the data structure for storing FASTA records

# Author name: Joshua Green
def parse_file(path: Path | str) -> list[FastaRecord]:
    """Parse a FASTA file from a filesystem path."""
    
    path = Path(path)  # Ensure the input is converted to a Path object

    # Open the file in read mode with UTF-8 encoding
    with path.open("r", encoding="utf-8") as f:
        text = f.read()  # Read entire file content as a string

    return parse_text(text)  # Delegate parsing logic to parse_text()


# Author name: Joshua Green
def parse_text(text: str) -> list[FastaRecord]:
    """Parse FASTA from a raw string."""
    
    records: list[FastaRecord] = []  # List to store parsed FASTA records
    header: str | None = None  # Stores current header line (without '>')
    sequence_lines: list[str] = []  # Stores sequence lines for current record

    # Iterate through each line in the input text
    for line in text.splitlines():
        line = line.strip()  # Remove leading/trailing whitespace

        if not line:
            continue  # Skip empty lines

        if line.startswith(">"):
            # If we encounter a new header, save the previous record first
            if header is not None:
                # Join sequence lines, remove spaces, and convert to uppercase
                sequence = "".join(sequence_lines).replace(" ", "").upper()
                
                # Extract record ID (first token in header)
                record_id = header.split()[0]
                
                # Create and store the FastaRecord object
                records.append(FastaRecord(
                    id=record_id,
                    description=header,
                    sequence=sequence
                ))

            # Start a new record
            header = line[1:].strip()  # Remove '>' and store header
            sequence_lines = []  # Reset sequence accumulator

        else:
            # If not a header, this line is part of the sequence
            sequence_lines.append(line)

    # After loop ends, add the final record (if any)
    if header is not None:
        sequence = "".join(sequence_lines).replace(" ", "").upper()
        record_id = header.split()[0]
        records.append(FastaRecord(
            id=record_id,
            description=header,
            sequence=sequence
        ))

    return records  # Return list of parsed FASTA records
