"""FASTA file parser.

Handles multi-sequence files, sequences split across lines,
whitespace within sequences, and mixed case normalization.
"""

from pathlib import Path

from ghostframe.models import FastaRecord


def parse_file(path: Path | str) -> list[FastaRecord]:
    """Parse a FASTA file from a filesystem path.

    Args:
        path: Path to a FASTA file.

    Returns:
        List of FastaRecord objects with sequences normalized to uppercase.

    Hints:
        - Read the file and delegate to parse_text().
    """
    raise NotImplementedError("FASTA file parsing not yet implemented")


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
    raise NotImplementedError("FASTA text parsing not yet implemented")
