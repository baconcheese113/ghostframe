"""Remote sequence retrieval via Ensembl REST API.

Fallback for when no local reference FASTA is available.
Future dependency: httpx for async HTTP requests.

Pipeline position: variants.normalize → [seqfetch.remote] → orfs
"""


def fetch(chrom: str, start: int, end: int) -> str:
    """Fetch a sequence region from the Ensembl REST API.

    Args:
        chrom: Chromosome name.
        start: 1-based start position.
        end: 1-based end position (inclusive).

    Returns:
        DNA sequence string.
    """
    raise NotImplementedError("Remote sequence fetch not yet implemented")
