"""ClinVar variant significance lookup.

Checks clinical significance of variants in the ClinVar database
via NCBI E-utilities (esearch + esummary).

Pipeline position: reclassify → [evidence.clinvar] → reports
"""

import os
from typing import Any

import httpx

from ghostframe.models import ClinVarHit, NormalizedVariant

_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _api_params() -> dict[str, str]:
    """Return base params, including api_key if available."""
    key = os.environ.get("NCBI_API_KEY", "")
    return {"api_key": key} if key else {}


def lookup(variant: NormalizedVariant) -> ClinVarHit | None:
    """Look up a variant in ClinVar via NCBI E-utilities.

    Returns typed clinical significance, review status, traits,
    oncogenicity, and the raw ClinVar accession — or None if not found.

    Args:
        variant: Variant to search for.

    Returns:
        Parsed ClinVar record if found, None otherwise.
    """
    base = _api_params()
    term = f"{variant.chrom}[Chromosome] AND {variant.pos}[Base Position For Assembly]"
    search = httpx.get(
        f"{_EUTILS}/esearch.fcgi",
        params={**base, "db": "clinvar", "term": term, "retmode": "json"},
        timeout=10.0,
    )
    search.raise_for_status()
    ids = search.json()["esearchresult"]["idlist"]
    if not ids:
        return None
    summary = httpx.get(
        f"{_EUTILS}/esummary.fcgi",
        params={
            **base,
            "db": "clinvar",
            "id": ",".join(ids[:5]),
            "retmode": "json",
        },
        timeout=10.0,
    )
    summary.raise_for_status()
    data: dict[str, Any] = summary.json().get("result", {})
    uids: list[str] = data.get("uids", [])
    if not uids:
        return None
    record: dict[str, Any] = data[uids[0]]
    germline: dict[str, Any] = record.get("germline_classification", {})
    oncogenicity: dict[str, Any] = record.get("oncogenicity_classification", {})
    traits = [
        trait_name
        for ts in germline.get("trait_set", [])
        if isinstance(ts, dict)
        for trait_name in [ts.get("trait_name")]  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        if isinstance(trait_name, str)
    ]
    genes = [
        symbol
        for gene in record.get("genes", [])
        if isinstance(gene, dict)
        for symbol in [gene.get("symbol")]  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
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
