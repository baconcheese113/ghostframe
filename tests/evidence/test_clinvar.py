from collections.abc import Generator
from unittest.mock import patch

import httpx
import pytest

from ghostframe.evidence import clinvar
from ghostframe.models import NormalizedVariant


def _make_variant() -> NormalizedVariant:
    return NormalizedVariant(
        chrom="13",
        pos=32333065,
        ref="A",
        alt="AA",
        classification="Silent",
        gene="BRCA2",
    )


def _response(
    status_code: int,
    payload: dict[str, object],
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        headers=headers,
        request=httpx.Request("GET", "https://eutils.ncbi.nlm.nih.gov/"),
    )


@pytest.fixture(autouse=True)
def _reset_rate_limit_state() -> Generator[None]:
    clinvar._NEXT_REQUEST_AT = 0.0
    yield
    clinvar._NEXT_REQUEST_AT = 0.0


@patch("ghostframe.evidence.clinvar.time.sleep", return_value=None)
@patch("ghostframe.evidence.clinvar._wait_for_rate_limit", return_value=None)
def test_lookup_retries_429_then_succeeds(
    _mock_rate_limit: object,
    _mock_sleep: object,
) -> None:
    warnings: list[str] = []
    with patch(
        "ghostframe.evidence.clinvar.httpx.get",
        side_effect=[
            _response(429, {}, headers={"Retry-After": "0"}),
            _response(200, {"esearchresult": {"idlist": ["1"]}}),
            _response(
                200,
                {
                    "result": {
                        "uids": ["1"],
                        "1": {
                            "accession": "RCV000000001",
                            "title": "Example ClinVar record",
                            "germline_classification": {
                                "description": "Pathogenic",
                                "review_status": "reviewed",
                                "last_evaluated": "2024-01-01",
                                "trait_set": [{"trait_name": "Breast cancer"}],
                            },
                            "oncogenicity_classification": {"description": "Oncogenic"},
                            "genes": [{"symbol": "BRCA2"}],
                            "molecular_consequence_list": ["missense variant"],
                            "obj_type": "single nucleotide variant",
                        },
                    }
                },
            ),
        ],
    ) as mock_get:
        result = clinvar.lookup(_make_variant(), warning_callback=warnings.append)

    assert result is not None
    assert result.accession == "RCV000000001"
    assert mock_get.call_count == 3
    assert warnings == []


@patch("ghostframe.evidence.clinvar.time.sleep", return_value=None)
@patch("ghostframe.evidence.clinvar._wait_for_rate_limit", return_value=None)
def test_lookup_returns_warning_after_exhausting_429_retries(
    _mock_rate_limit: object,
    _mock_sleep: object,
) -> None:
    warnings: list[str] = []
    with patch(
        "ghostframe.evidence.clinvar.httpx.get",
        side_effect=[
            _response(429, {}, headers={"Retry-After": "0"}),
            _response(429, {}, headers={"Retry-After": "0"}),
            _response(429, {}, headers={"Retry-After": "0"}),
            _response(429, {}, headers={"Retry-After": "0"}),
        ],
    ) as mock_get:
        result = clinvar.lookup(_make_variant(), warning_callback=warnings.append)

    assert result is None
    assert mock_get.call_count == 4
    assert warnings == ["ClinVar rate-limited the request; continuing without ClinVar evidence."]


@patch("ghostframe.evidence.clinvar.time.sleep", return_value=None)
@patch("ghostframe.evidence.clinvar._wait_for_rate_limit", return_value=None)
def test_lookup_returns_warning_for_non_retriable_client_error(
    _mock_rate_limit: object,
    _mock_sleep: object,
) -> None:
    warnings: list[str] = []
    with patch(
        "ghostframe.evidence.clinvar.httpx.get",
        return_value=_response(400, {}),
    ) as mock_get:
        result = clinvar.lookup(_make_variant(), warning_callback=warnings.append)

    assert result is None
    assert mock_get.call_count == 1
    assert warnings == [
        "ClinVar request failed with HTTP 400; continuing without ClinVar evidence."
    ]


@pytest.mark.integration
@pytest.mark.slow
def test_lookup_known_variant_returns_parsed_hit():
    result = clinvar.lookup(_make_variant())
    assert result is not None
    assert result.accession is not None
    assert result.germline_significance is not None
    assert isinstance(result.traits, list)


@pytest.mark.integration
@pytest.mark.slow
def test_lookup_bogus_position_returns_none():
    v = NormalizedVariant(
        chrom="99",
        pos=999999999,
        ref="A",
        alt="T",
        classification="Silent",
        gene="UNKNOWN",
    )
    assert clinvar.lookup(v) is None
