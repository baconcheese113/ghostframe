"""Remote sequence retrieval via Ensembl REST API.

Fallback for when no local reference FASTA is available.

Pipeline position: variants.normalize → [seqfetch.remote] → orfs
"""

import httpx

_ENSEMBL_REST = "https://rest.ensembl.org"


def fetch(chrom: str, start: int, end: int) -> str:
    """Fetch a sequence region from the Ensembl REST API.

    Args:
        chrom: Chromosome name (e.g. "1", "X").
        start: 1-based start position.
        end: 1-based end position (inclusive).

    Returns:
        Uppercase DNA sequence string.
    """
    url = f"{_ENSEMBL_REST}/sequence/region/human/{chrom}:{start}..{end}"
    response = httpx.get(url, headers={"Accept": "text/plain"}, follow_redirects=True)
    response.raise_for_status()
    print(f"Fetched sequence from Ensembl: {chrom}:{start}-{end} ({len(response.text.strip())} bp)")
    return response.text.strip().upper()
