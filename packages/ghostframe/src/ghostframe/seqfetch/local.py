"""Local FASTA sequence retrieval.

Fetches sequence regions from a local indexed FASTA file.
Future dependency: pysam or pyfaidx for indexed access.

Pipeline position: variants.normalize → [seqfetch.local] → orfs
"""

from pathlib import Path


def fetch(chrom: str, start: int, end: int, ref_path: Path) -> str:
    """Fetch a sequence region from a local indexed FASTA.

    Args:
        chrom: Chromosome name.
        start: 0-based start position.
        end: 0-based end position (exclusive).
        ref_path: Path to the reference FASTA file.

    Returns:
        DNA sequence string.
    """
    raise NotImplementedError("Local sequence fetch not yet implemented")
