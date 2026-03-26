"""SynMICdb synonymous mutation lookup.

Checks variant recurrence and scores in the SynMICdb database of
synonymous mutations in cancer. Uses a local copy of the dataset from:

    Sharma et al., Nature Communications (2019)
    https://doi.org/10.1038/s41467-019-10489-2

Dataset sourced from the OpenVar GitHub repository:
    https://github.com/MAB-Lab/OpenVar

Pipeline position: reclassify → [evidence.synmicdb] → reports
"""

from importlib.resources import files
from typing import Any

import pandas as pd

from ghostframe.models import NormalizedVariant, SynMICdbHit

_DATA_REF = files("ghostframe.evidence") / "data" / "cancer_syn_fullData.csv.zip"

_cache: pd.DataFrame | None = None

_KEEP_COLS = [
    "Gene Name",
    "Transcript ID",
    "Mutation ID",
    "Mutation nt",
    "Mutation aa",
    "Mutation Genome Position",
    "Chromosome",
    "Start",
    "End",
    "Strand",
    "Signature-normalized Frequency",
    "Average Mutation Load",
    "Alternative Events",
    "SNP",
    "Conservation",
    "Structure Change Score (remuRNA)",
    "Structure Change Significance (RNAsnp)",
    "SynMICdb Score",
]


def _load() -> pd.DataFrame:
    """Lazy-load, deduplicate, and cache the SynMICdb dataset."""
    global _cache
    if _cache is not None:
        return _cache
    data_path = _DATA_REF
    if not data_path.is_file():
        raise FileNotFoundError(
            "SynMICdb dataset not found at expected location. The file "
            "cancer_syn_fullData.csv.zip should be committed in "
            "packages/ghostframe/src/ghostframe/evidence/data/"
        )
    df = pd.read_csv(str(data_path), compression="zip", usecols=_KEEP_COLS, low_memory=False)
    df = df.drop_duplicates(subset=["Mutation ID"]).copy()
    df["Chromosome"] = df["Chromosome"].astype(str).str.removeprefix("chr")
    df["Start"] = pd.to_numeric(df["Start"], errors="coerce")
    df["SynMICdb Score"] = pd.to_numeric(df["SynMICdb Score"], errors="coerce")
    _cache = df
    return _cache


def _optional_float(value: Any) -> float | None:
    """Return a float for non-null pandas values."""
    if pd.isna(value):
        return None
    return float(value)


def _optional_str(value: Any) -> str | None:
    """Return a string for non-null pandas values."""
    if pd.isna(value):
        return None
    return str(value)


def lookup(variant: NormalizedVariant) -> SynMICdbHit | None:
    """Look up a variant in the local SynMICdb dataset.

    Matches by (chrom, pos), disambiguates by gene. Returns the highest-scored
    match as a typed hit, or None if no match is found.

    Args:
        variant: Variant to search for.

    Returns:
        SynMICdb record if found, None otherwise.
    """
    df = _load()
    chrom = variant.chrom.removeprefix("chr")
    hits = df[(df["Chromosome"] == chrom) & (df["Start"] == variant.pos)]
    if hits.empty:
        return None
    if variant.gene:
        gene_hits = hits[hits["Gene Name"].str.upper() == variant.gene.upper()]
        if not gene_hits.empty:
            hits = gene_hits
    best = hits.sort_values("SynMICdb Score", ascending=False).iloc[0]
    return SynMICdbHit(
        gene_name=str(best["Gene Name"]),
        transcript_id=str(best["Transcript ID"]),
        mutation_id=str(best["Mutation ID"]),
        mutation_nt=str(best["Mutation nt"]),
        mutation_aa=str(best["Mutation aa"]),
        genome_position=str(best["Mutation Genome Position"]),
        chrom=str(best["Chromosome"]),
        start=int(best["Start"]) if pd.notna(best["Start"]) else 0,
        end=int(best["End"]) if pd.notna(best["End"]) else 0,
        strand=str(best["Strand"]),
        frequency=_optional_float(best["Signature-normalized Frequency"]),
        avg_mutation_load=_optional_float(best["Average Mutation Load"]),
        alternative_events=_optional_str(best["Alternative Events"]),
        snp=_optional_str(best["SNP"]),
        conservation=_optional_float(best["Conservation"]),
        structure_change_score=_optional_float(best["Structure Change Score (remuRNA)"]),
        structure_change_significance=_optional_float(
            best["Structure Change Significance (RNAsnp)"]
        ),
        score=_optional_float(best["SynMICdb Score"]),
    )
