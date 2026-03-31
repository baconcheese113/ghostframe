"""ClinVar variant significance lookup.

Checks clinical significance of variants in the ClinVar database
via NCBI E-utilities (esearch + esummary).

Pipeline position: reclassify -> [evidence.clinvar] -> reports
"""

import os
import threading
import time
from collections.abc import Callable
from typing import Any

import httpx

from ghostframe.models import ClinVarHit, NormalizedVariant

_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_REQUEST_TIMEOUT_SECONDS = 10.0
_MAX_ATTEMPTS = 4
_INITIAL_BACKOFF_SECONDS = 1.0
_MAX_BACKOFF_SECONDS = 8.0
_RATE_LIMIT_LOCK = threading.Lock()
_NEXT_REQUEST_AT = 0.0

type _WarningCallback = Callable[[str], None]


def _api_params() -> dict[str, str]:
    """Return base params, including NCBI identification values if available."""
    params: dict[str, str] = {}

    api_key = os.environ.get("NCBI_API_KEY", "").strip()
    if api_key:
        params["api_key"] = api_key

    email = os.environ.get("NCBI_EMAIL", "").strip()
    if email:
        params["email"] = email

    tool = os.environ.get("NCBI_TOOL", "").strip()
    if tool:
        params["tool"] = tool

    return params


def _request_interval_seconds() -> float:
    return 0.1 if os.environ.get("NCBI_API_KEY", "").strip() else (1.0 / 3.0)


def _wait_for_rate_limit() -> None:
    global _NEXT_REQUEST_AT

    with _RATE_LIMIT_LOCK:
        now = time.monotonic()
        if now < _NEXT_REQUEST_AT:
            time.sleep(_NEXT_REQUEST_AT - now)
            now = time.monotonic()
        _NEXT_REQUEST_AT = now + _request_interval_seconds()


def _warn(warning_callback: _WarningCallback | None, message: str) -> None:
    if warning_callback is not None:
        warning_callback(message)


def _retry_delay_seconds(exc: httpx.HTTPStatusError, fallback: float) -> float:
    retry_after = exc.response.headers.get("Retry-After", "")
    if retry_after.isdigit():
        return min(float(retry_after), _MAX_BACKOFF_SECONDS)
    return fallback


def _request_json(
    endpoint: str,
    params: dict[str, str],
    warning_callback: _WarningCallback | None,
) -> dict[str, Any] | None:
    delay = _INITIAL_BACKOFF_SECONDS
    url = f"{_EUTILS}/{endpoint}"

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            _wait_for_rate_limit()
            response = httpx.get(
                url,
                params=params,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            retriable = status_code == 429 or status_code >= 500
            if retriable and attempt < _MAX_ATTEMPTS:
                time.sleep(_retry_delay_seconds(exc, delay))
                delay = min(delay * 2, _MAX_BACKOFF_SECONDS)
                continue

            if status_code == 429:
                _warn(
                    warning_callback,
                    "ClinVar rate-limited the request; continuing without ClinVar evidence.",
                )
            else:
                _warn(
                    warning_callback,
                    (
                        f"ClinVar request failed with HTTP {status_code}; "
                        "continuing without ClinVar evidence."
                    ),
                )
            return None
        except httpx.RequestError:
            if attempt < _MAX_ATTEMPTS:
                time.sleep(delay)
                delay = min(delay * 2, _MAX_BACKOFF_SECONDS)
                continue

            _warn(
                warning_callback,
                "ClinVar could not be reached after retries; continuing without ClinVar evidence.",
            )
            return None
        except Exception:
            _warn(
                warning_callback,
                "ClinVar returned an unexpected response; continuing without ClinVar evidence.",
            )
            return None

    return None


def lookup(
    variant: NormalizedVariant,
    warning_callback: _WarningCallback | None = None,
) -> ClinVarHit | None:
    """Look up a variant in ClinVar via NCBI E-utilities.

    Returns typed clinical significance, review status, traits,
    oncogenicity, and the raw ClinVar accession, or None if not found.

    Args:
        variant: Variant to search for.
        warning_callback: Optional callback for non-fatal network/API warnings.

    Returns:
        Parsed ClinVar record if found, None otherwise.
    """
    base = _api_params()
    term = f"{variant.chrom}[Chromosome] AND {variant.pos}[Base Position For Assembly]"
    search_data = _request_json(
        "esearch.fcgi",
        params={**base, "db": "clinvar", "term": term, "retmode": "json"},
        warning_callback=warning_callback,
    )
    if search_data is None:
        return None

    ids = search_data.get("esearchresult", {}).get("idlist", [])
    if not isinstance(ids, list) or not ids:
        return None

    summary_data = _request_json(
        "esummary.fcgi",
        params={
            **base,
            "db": "clinvar",
            "id": ",".join(ids[:5]),
            "retmode": "json",
        },
        warning_callback=warning_callback,
    )
    if summary_data is None:
        return None

    data = summary_data.get("result", {})
    if not isinstance(data, dict):
        return None

    uids = data.get("uids", [])
    if not isinstance(uids, list) or not uids:
        return None

    record = data.get(uids[0], {})
    if not isinstance(record, dict):
        return None

    germline = record.get("germline_classification", {})
    oncogenicity = record.get("oncogenicity_classification", {})
    if not isinstance(germline, dict):
        germline = {}
    if not isinstance(oncogenicity, dict):
        oncogenicity = {}

    traits = [
        trait_name
        for trait_set in germline.get("trait_set", [])
        if isinstance(trait_set, dict)
        for trait_name in [trait_set.get("trait_name")]
        if isinstance(trait_name, str)
    ]
    genes = [
        symbol
        for gene in record.get("genes", [])
        if isinstance(gene, dict)
        for symbol in [gene.get("symbol")]
        if isinstance(symbol, str)
    ]
    molecular_consequences = [
        consequence
        for consequence in record.get("molecular_consequence_list", [])
        if isinstance(consequence, str)
    ]

    return ClinVarHit(
        accession=record.get("accession"),
        title=record.get("title"),
        germline_significance=germline.get("description"),
        germline_review_status=germline.get("review_status"),
        germline_last_evaluated=germline.get("last_evaluated"),
        traits=traits,
        oncogenicity=oncogenicity.get("description"),
        molecular_consequences=molecular_consequences,
        genes=genes,
        variant_type=record.get("obj_type"),
    )
