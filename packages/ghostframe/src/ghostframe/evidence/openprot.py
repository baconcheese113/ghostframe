"""OpenProt alternative ORF annotation lookup.

Checks whether discovered ORFs match known alternative ORFs in the
OpenProt 2.0 database via its REST API.

Pipeline position: reclassify → [evidence.openprot] → reports
"""

import re

import httpx

from ghostframe.models import ORF, OpenProtHit

_BASE = "https://api.openprot.org/api/2.0/HS"


def lookup(orf: ORF, gene: str) -> OpenProtHit | None:
    """Look up an ORF against the OpenProt 2.0 database by gene symbol.

    Searches the OpenProt REST API for proteins of ``gene``, filters to exact
    gene-symbol matches, then fetches full details for the top-scored hit.
    The returned hit includes ``sequence``, ``segments`` (exon coords), and
    genomic location — ready for sequence-level ORF matching once
    ``ghostframe.orfs.sequence.translate`` is no longer stubbed.

    Args:
        orf: ORF to look up (reserved for future sequence matching).
        gene: HGNC gene symbol, e.g. "TP53".

    Returns:
        Full OpenProt protein details for the top hit, or None.
    """
    resp = httpx.get(f"{_BASE}/search_proteins/a/{gene}", timeout=10.0)
    resp.raise_for_status()
    pattern = re.compile(r"gs:" + re.escape(gene) + r"\*")
    matches = [p for p in resp.json() if pattern.search(p.get("searchable_accessions", ""))]
    if not matches:
        return None
    top = max(matches, key=lambda p: p.get("combined_evidence_score", 0))
    details_resp = httpx.get(f"{_BASE}/proteins/{top['protein_seq_id']}/details", timeout=10.0)
    details_resp.raise_for_status()
    records = details_resp.json()
    if not records:
        return None
    rec = records[0]
    return OpenProtHit(
        accession=str(rec.get("accession", "")),
        protein_type=str(rec.get("type", "")),
        symbol=rec.get("symbol"),
        gene_accession=rec.get("gene_accession"),
        chrom=rec.get("location_chr"),
        start=rec.get("location_start"),
        end=rec.get("location_end"),
        strand=rec.get("strand"),
        sequence=rec.get("sequence"),
        iep=rec.get("iep"),
        weight=rec.get("weight"),
        uniprot_accessions=rec.get("uniprot_accessions"),
        segments=rec.get("segments"),
    )
