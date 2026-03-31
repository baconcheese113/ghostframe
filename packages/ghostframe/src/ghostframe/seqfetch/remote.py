"""Remote sequence retrieval via Ensembl REST API.

Fallback for when no local reference FASTA is available.

Pipeline position: variants.normalize → [seqfetch.remote] → orfs
"""

import asyncio

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

_ENSEMBL_REST = "https://rest.ensembl.org"
_BATCH_ENDPOINT = f"{_ENSEMBL_REST}/sequence/region/human"
_BATCH_SIZE = 50


def _normalize_chrom(chrom: str) -> str:
    """Strip 'chr' prefix; map chrM/chrMT → MT for Ensembl."""
    chrom = chrom.removeprefix("chr")
    if chrom in ("M", "MT"):
        return "MT"
    return chrom


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
    response = httpx.get(url, headers={"Accept": "text/plain"}, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    print(f"Fetched sequence from Ensembl: {chrom}:{start}-{end} ({len(response.text.strip())} bp)")
    return response.text.strip().upper()


@retry(
    retry=retry_if_exception(
        lambda e: isinstance(e, httpx.HTTPStatusError)
        and e.response.status_code in (429, 503)
    ),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(4),
    reraise=True,
)
async def _post_batch(
    client: httpx.AsyncClient,
    regions: list[str],
) -> list[dict]:
    """POST a single batch of <=50 region strings to Ensembl."""
    resp = await client.post(
        _BATCH_ENDPOINT,
        json={"regions": regions},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


async def fetch_batch(
    regions: list[tuple[str, int, int]],
    *,
    concurrency: int = 3,
) -> dict[tuple[str, int, int], str]:
    """Fetch multiple sequence windows from Ensembl in batched concurrent POSTs.

    Args:
        regions: List of (chrom, 1-based-start, 1-based-end) tuples.
                 chrom may include 'chr' prefix; chrM/chrMT are mapped to MT.
        concurrency: Max simultaneous POST requests (default 3).

    Returns:
        Dict mapping each input (norm_chrom, start, end) tuple to its uppercase sequence.
    """
    if not regions:
        return {}

    # Build region strings and an index back to normalized tuples
    region_strings: list[str] = []
    index: list[tuple[str, int, int]] = []
    for chrom, start, end in regions:
        norm = _normalize_chrom(chrom)
        region_strings.append(f"{norm}:{start}..{end}")
        index.append((norm, start, end))

    # Chunk into batches of _BATCH_SIZE
    batches: list[list[str]] = [
        region_strings[i : i + _BATCH_SIZE]
        for i in range(0, len(region_strings), _BATCH_SIZE)
    ]
    batch_indices: list[list[tuple[str, int, int]]] = [
        index[i : i + _BATCH_SIZE]
        for i in range(0, len(index), _BATCH_SIZE)
    ]

    semaphore = asyncio.Semaphore(concurrency)
    results: dict[tuple[str, int, int], str] = {}

    async def fetch_one_batch(
        client: httpx.AsyncClient,
        batch_regions: list[str],
        batch_keys: list[tuple[str, int, int]],
    ) -> None:
        async with semaphore:
            data = await _post_batch(client, batch_regions)
        for key, item in zip(batch_keys, data):
            seq = item.get("seq", "")
            results[key] = seq.upper()
            print(
                f"Fetched sequence from Ensembl (batch): "
                f"{key[0]}:{key[1]}-{key[2]} ({len(seq)} bp)"
            )

    async with httpx.AsyncClient() as client:
        await asyncio.gather(
            *[fetch_one_batch(client, b, k) for b, k in zip(batches, batch_indices)]
        )
    return results
