"""Tests for seqfetch.remote batch fetch and chromosome normalization."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from ghostframe.seqfetch.remote import _normalize_chrom, fetch_batch


# ---------------------------------------------------------------------------
# _normalize_chrom
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [
    ("chr1", "1"),
    ("chrX", "X"),
    ("chrY", "Y"),
    ("chr22", "22"),
    ("chrM", "MT"),
    ("chrMT", "MT"),
    ("1", "1"),
    ("X", "X"),
    ("MT", "MT"),
])
def test_normalize_chrom(raw, expected):
    assert _normalize_chrom(raw) == expected


# ---------------------------------------------------------------------------
# fetch_batch — chunking
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_fetch_batch_empty_returns_empty():
    result = await fetch_batch([])
    assert result == {}


@pytest.mark.anyio
async def test_fetch_batch_chunks_51_regions_into_two_posts():
    """51 regions should trigger exactly 2 POST calls (50 + 1)."""
    regions = [("1", i, i + 1000) for i in range(1, 52)]

    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        batch = kwargs["json"]["regions"]
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = [{"seq": "A" * 1001} for _ in batch]
        return response

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = fake_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await fetch_batch(regions)

    assert call_count == 2


# ---------------------------------------------------------------------------
# fetch_batch — return value
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_fetch_batch_returns_uppercase_sequences():
    regions = [("chr1", 1000, 2000), ("chrX", 5000, 6000)]

    async def fake_post(url, **kwargs):
        batch = kwargs["json"]["regions"]
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = [{"seq": "atcg" * 250} for _ in batch]
        return response

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = fake_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await fetch_batch(regions)

    assert result[("1", 1000, 2000)] == ("ATCG" * 250)
    assert result[("X", 5000, 6000)] == ("ATCG" * 250)


# ---------------------------------------------------------------------------
# fetch_batch — tenacity retry on 429
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_fetch_batch_retries_on_429():
    """Two 429 responses followed by a 200 should succeed after 3 total calls."""
    regions = [("1", 1000, 2000)]
    call_count = 0

    async def fake_post(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            error_response = MagicMock()
            error_response.status_code = 429
            raise httpx.HTTPStatusError("rate limited", request=MagicMock(), response=error_response)
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = [{"seq": "ACGT" * 250}]
        return response

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.side_effect = fake_post
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        # Speed up tenacity waits in tests
        with patch("tenacity.nap.sleep"):
            result = await fetch_batch(regions)

    assert call_count == 3
    assert result[("1", 1000, 2000)] == "ACGT" * 250


# ---------------------------------------------------------------------------
# Integration — real Ensembl call (skipped unless --run-integration)
# ---------------------------------------------------------------------------

@pytest.mark.integration
async def test_fetch_batch_real_ensembl():
    """Fetch a known 1001 bp window from Ensembl (requires network)."""
    result = await fetch_batch([("1", 1000000, 1001000)])
    seq = result[("1", 1000000, 1001000)]
    assert len(seq) == 1001
    assert set(seq) <= {"A", "T", "C", "G", "N"}
