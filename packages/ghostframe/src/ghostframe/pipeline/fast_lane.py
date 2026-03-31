"""Fast lane pipeline — synchronous, seconds-scale analysis.

intake → filter → coordinate normalization → sequence fetch →
6-frame ORF scan → reclassification → cohort summary stats.

Powers the dashboard immediately.
"""

from pathlib import Path

from ghostframe.models import FastLaneResult, FrameEffect
from ghostframe.orfs.scanner import find_orfs
from ghostframe.reclassify import engine
from ghostframe.reclassify import summary as summary_mod
from ghostframe.seqfetch import local
from ghostframe.seqfetch import window as window_mod
from ghostframe.variants import filters, maf, normalize


def run(
    maf_path: Path,
    fasta_path: Path | None,
    min_len: int = 50,
) -> FastLaneResult:
    """Run the synchronous fast analysis pipeline.

    Args:
        maf_path: Path to the input MAF file.
        fasta_path: Path to the reference FASTA. Required for local sequence
            fetch; pass None only if remote fetch is implemented (not yet).
        min_len: Minimum ORF length in bases for scanning.

    Returns:
        FastLaneResult with summary statistics, Sankey data, and
        per-variant reclassification results.
    """
    if fasta_path is None:
        raise ValueError("fasta_path is required (remote fetch not yet implemented)")

    variants = maf.parse(maf_path)
    silent = filters.keep_silent(variants)
    normalized = [normalize.normalize(v) for v in silent]

    # Cache full chromosome sequences to avoid redundant FASTA reads
    seq_cache: dict[str, str] = {}

    all_effects: list[FrameEffect] = []
    for variant in normalized:
        if variant.chrom not in seq_cache:
            seq_cache[variant.chrom] = local.fetch(variant.chrom, 0, 10**9, fasta_path)
        full_seq = seq_cache[variant.chrom]

        window = window_mod.extract(variant, full_seq)
        orfs = find_orfs(window.sequence, min_len)
        effects = engine.reclassify(variant, orfs, window)
        for e in effects:
            e.variant = variant
        all_effects.extend(effects)

    result_summary = summary_mod.aggregate(all_effects)
    return FastLaneResult(
        summary=result_summary,
        sankey_data=result_summary.sankey_data,
        reclassified_variants=all_effects,
    )
