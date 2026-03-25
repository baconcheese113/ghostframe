"""Local FASTA sequence retrieval.

Fetches sequence regions from a local indexed FASTA file using pyfaidx.

Pipeline position: variants.normalize → [seqfetch.local] → orfs
"""

from pathlib import Path
from typing import Any

from pyfaidx import Fasta  # type: ignore[import-untyped]


def fetch(chrom: str, start: int, end: int, ref_path: Path) -> str:
    """Fetch a sequence region from a local indexed FASTA.

    Args:
        chrom: Chromosome name.
        start: 0-based start position.
        end: 0-based end position (exclusive).
        ref_path: Path to the reference FASTA file.

    Returns:
        Uppercase DNA sequence string.
    """
    fasta: Any = Fasta(str(ref_path))
    try:
        return str(fasta[chrom][start:end]).upper()
    finally:
        fasta.close()
