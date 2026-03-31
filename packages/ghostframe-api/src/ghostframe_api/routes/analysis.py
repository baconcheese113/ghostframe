"""Analysis endpoints - submit jobs and retrieve results."""

import asyncio
import json
import tempfile
import time
import uuid
from collections.abc import Sequence
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ghostframe.models import (
    FastLaneResult,
    FrameEffect,
    GenomicWindow,
    ReclassifySummary,
    ScoredCandidate,
)
from ghostframe.orfs.scanner import find_orfs
from ghostframe.pipeline import deep_lane
from ghostframe.reclassify import engine
from ghostframe.reclassify import summary as summary_mod
from ghostframe.seqfetch import local
from ghostframe.seqfetch import remote as remote_mod
from ghostframe.seqfetch import window as window_mod
from ghostframe.variants import filters, maf, normalize
from ghostframe_api.config import Settings
from ghostframe_api.schemas import AnalysisRequest

router = APIRouter()
_settings = Settings()
_DEFAULT_HLA_ALLELES = ["HLA-A*02:01"]


def _effect_to_dict(effect: FrameEffect, window_size: int, variant_in_window: int) -> dict:
    variant = effect.variant
    gene = variant.gene if variant else ""
    pos = variant.pos if variant else abs(effect.orf.pos)
    return {
        "id": f"{gene}_{effect.orf.frame}_{pos}",
        "gene": gene,
        "position": pos,
        "frame": effect.orf.frame,
        "old_class": "Silent",
        "new_class": effect.new_class,
        "ref_codon": effect.ref_codon,
        "alt_codon": effect.alt_codon,
        "ref_aa": effect.ref_aa,
        "alt_aa": effect.alt_aa,
        "evidence_tier": effect.evidence_tier,
        "synmicdb_score": effect.synmicdb_score,
        "clinvar_significance": None,
        "narrative": "",
        "peptides": [],
        "orf_dna": effect.orf.dna,
        "orf_pos": effect.orf.pos,
        "orf_length": effect.orf.length,
        "window_size": window_size,
        "variant_in_window": variant_in_window,
        "codon_pos": effect.codon_pos,
        "chrom": variant.chrom if variant else "",
        "ref": variant.ref if variant else "",
        "alt": variant.alt if variant else "",
    }


def _candidate_variant_id(effect: FrameEffect) -> str:
    variant = effect.variant
    pos = variant.pos if variant else abs(effect.orf.pos)
    gene = variant.gene if variant else ""
    return f"{gene}_{effect.orf.frame}_{pos}"


def _event_int(event: dict[str, object], key: str) -> int:
    value = event.get(key)
    return value if isinstance(value, int) else 0


def _event_str(event: dict[str, object], key: str) -> str | None:
    value = event.get(key)
    return value if isinstance(value, str) else None


def _event_optional_int(event: dict[str, object], key: str) -> int | None:
    value = event.get(key)
    return value if isinstance(value, int) else None


def _format_elapsed_ms(elapsed_ms: int) -> str:
    if elapsed_ms >= 60_000:
        minutes, remainder = divmod(elapsed_ms, 60_000)
        return f"{minutes}m {remainder / 1000:.1f}s"
    return f"{elapsed_ms / 1000:.2f}s"


def _log_step(name: str, detail: str, elapsed_ms: int) -> None:
    print(f"[analysis] {name}: {detail} ({_format_elapsed_ms(elapsed_ms)})")


def _safe_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    name = Path(filename).name.strip()
    return name or None


def _count_label(count: int, singular: str, plural: str | None = None) -> str:
    plural_label = plural or f"{singular}s"
    noun = singular if count == 1 else plural_label
    return f"{count} {noun}"


def _build_analysis_meta(
    *,
    variants: Sequence[object],
    maf_filename: str | None,
    is_demo: bool,
    hla_alleles: list[str],
) -> dict[str, object]:
    sample_barcodes = sorted(
        {
            barcode
            for variant in variants
            for barcode in [getattr(variant, "sample_barcode", None)]
            if barcode
        }
    )
    variant_count = len(variants)
    safe_filename = _safe_filename(maf_filename)

    if len(sample_barcodes) == 1:
        primary_label = sample_barcodes[0]
        secondary_label = safe_filename or _count_label(variant_count, "variant")
    elif safe_filename:
        primary_label = safe_filename
        if len(sample_barcodes) > 1:
            secondary_label = (
                f"{_count_label(len(sample_barcodes), 'sample')} / "
                f"{_count_label(variant_count, 'variant')}"
            )
        else:
            secondary_label = _count_label(variant_count, "variant")
    elif is_demo:
        primary_label = "Demo dataset"
        secondary_label = _count_label(variant_count, "variant")
    else:
        primary_label = "Uploaded MAF"
        if len(sample_barcodes) > 1:
            secondary_label = (
                f"{_count_label(len(sample_barcodes), 'sample')} / "
                f"{_count_label(variant_count, 'variant')}"
            )
        else:
            secondary_label = _count_label(variant_count, "variant")

    return {
        "primary_label": primary_label,
        "secondary_label": secondary_label,
        "sample_count": len(sample_barcodes),
        "variant_count": variant_count,
        "is_demo": is_demo,
        "hla_alleles": hla_alleles,
    }


def _build_fast_summary(
    *,
    total_input_variants: int,
    total_silent_variants: int,
    total_orfs: int,
    total_effects: int,
    reclassified_effects: int,
    frames_affected: int,
) -> dict[str, object]:
    return {
        "total_input_variants": total_input_variants,
        "total_silent_variants": total_silent_variants,
        "total_orfs": total_orfs,
        "total_effects": total_effects,
        "reclassified_effects": reclassified_effects,
        "total_silent": total_silent_variants,
        "reclassified": reclassified_effects,
        "frames_affected": frames_affected,
        "best_ic50": None,
    }


def _candidate_to_enrichment_event(candidate: ScoredCandidate, elapsed_ms: int) -> dict:
    evidence = candidate.evidence
    return {
        "type": "enrich_complete",
        "variant_id": _candidate_variant_id(candidate.effect),
        "elapsed_ms": elapsed_ms,
        "candidates": [
            {
                "peptide_sequence": (
                    candidate.binding.peptide.sequence if candidate.binding else None
                ),
                "allele": candidate.binding.allele if candidate.binding else None,
                "ic50": candidate.binding.affinity if candidate.binding else None,
                "rank": candidate.binding.rank if candidate.binding else None,
                "score": candidate.score,
                "domain_hits": [
                    {
                        "accession": hit.accession,
                        "name": hit.name,
                        "start": hit.start,
                        "end": hit.end,
                        "score": hit.score,
                    }
                    for hit in candidate.domain_hits
                ],
            }
        ],
        "evidence": {
            "tier": evidence.tier if evidence else 1,
            "openprot_accession": (
                evidence.openprot.accession if evidence and evidence.openprot else None
            ),
            "openprot_type": (
                evidence.openprot.protein_type if evidence and evidence.openprot else None
            ),
            "synmicdb_score": (evidence.synmicdb.score if evidence and evidence.synmicdb else None),
            "clinvar_significance": (
                evidence.clinvar.germline_significance if evidence and evidence.clinvar else None
            ),
        },
    }


@router.post("/analyze")
async def start_analysis(request: AnalysisRequest) -> StreamingResponse:
    """Run the full pipeline and stream progress events as NDJSON."""
    job_id = str(uuid.uuid4())[:8]

    async def generate():
        def emit(payload: dict) -> str:
            return json.dumps(payload) + "\n"

        tmp_path: Path | None = None
        try:
            maf_start = time.perf_counter()
            yield emit(
                {
                    "type": "running",
                    "name": "MAF / FASTA",
                    "detail": "Loading analysis input",
                    "elapsed_ms": 0,
                }
            )
            await asyncio.sleep(0)

            maf_path = _settings.demo_maf
            is_demo = request.maf_content is None
            if request.maf_content is not None:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".maf",
                    delete=False,
                    encoding="utf-8",
                ) as tmp:
                    tmp.write(request.maf_content)
                    tmp_path = Path(tmp.name)
                maf_path = tmp_path

            try:
                all_variants = maf.parse(maf_path)
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - maf_start) * 1000)
                yield emit(
                    {
                        "type": "step",
                        "name": "MAF / FASTA",
                        "status": "error",
                        "detail": str(exc),
                        "elapsed_ms": elapsed_ms,
                    }
                )
                yield emit({"type": "error", "error": str(exc)})
                return

            maf_elapsed_ms = int((time.perf_counter() - maf_start) * 1000)
            analysis_meta = _build_analysis_meta(
                variants=all_variants,
                maf_filename=request.maf_filename,
                is_demo=is_demo,
                hla_alleles=_DEFAULT_HLA_ALLELES,
            )
            maf_detail = f"{len(all_variants)} variants in {_format_elapsed_ms(maf_elapsed_ms)}"
            _log_step("MAF / FASTA", f"{len(all_variants)} variants", maf_elapsed_ms)
            yield emit(
                {
                    "type": "step",
                    "name": "MAF / FASTA",
                    "status": "success",
                    "detail": maf_detail,
                    "elapsed_ms": maf_elapsed_ms,
                }
            )
            await asyncio.sleep(0)

            filter_start = time.perf_counter()
            yield emit(
                {
                    "type": "running",
                    "name": "Filter Silent",
                    "detail": "Filtering and normalizing silent variants",
                    "elapsed_ms": 0,
                }
            )
            await asyncio.sleep(0)

            silent = filters.keep_silent(all_variants)
            normalized = [normalize.normalize(variant) for variant in silent]
            filter_elapsed_ms = int((time.perf_counter() - filter_start) * 1000)
            filter_detail = (
                f"{len(silent)} silent variants in {_format_elapsed_ms(filter_elapsed_ms)}"
            )
            _log_step("Filter Silent", f"{len(silent)} silent variants", filter_elapsed_ms)
            yield emit(
                {
                    "type": "step",
                    "name": "Filter Silent",
                    "status": "success",
                    "detail": filter_detail,
                    "elapsed_ms": filter_elapsed_ms,
                }
            )
            await asyncio.sleep(0)

            seq_fetch_start = time.perf_counter()
            yield emit(
                {
                    "type": "running",
                    "name": "Seq Fetch",
                    "detail": "Fetching reference sequence windows",
                    "elapsed_ms": 0,
                }
            )
            await asyncio.sleep(0)

            try:
                seq_cache: dict[str, str] = {}
                remote_windows: dict[str, GenomicWindow] = {}
                remote_chroms: set[str] = set()

                for variant in normalized:
                    if variant.chrom in seq_cache or variant.chrom in remote_chroms:
                        continue
                    try:
                        seq_cache[variant.chrom] = local.fetch(
                            variant.chrom,
                            0,
                            10**9,
                            _settings.demo_fasta,
                        )
                    except Exception:
                        remote_chroms.add(variant.chrom)

                if remote_chroms:
                    flank = 500
                    seen_win_keys: set[str] = set()
                    region_list: list[tuple[str, int, int]] = []
                    region_to_win: dict[tuple[str, int, int], tuple[str, str]] = {}

                    for variant in normalized:
                        if variant.chrom not in remote_chroms:
                            continue

                        win_key = f"{variant.chrom}_{variant.pos}"
                        if win_key in seen_win_keys:
                            continue

                        seen_win_keys.add(win_key)
                        window_start = max(0, variant.pos - 1 - flank)
                        window_end = variant.pos - 1 + len(variant.ref) + flank
                        chrom_ens = remote_mod._normalize_chrom(variant.chrom)
                        region_tuple = (chrom_ens, window_start + 1, window_end)
                        region_list.append(region_tuple)
                        region_to_win[region_tuple] = (win_key, variant.chrom)

                    fetched = await remote_mod.fetch_batch(region_list)
                    for region_tuple, sequence in fetched.items():
                        win_key, chrom_orig = region_to_win[region_tuple]
                        _, ens_start, ens_end = region_tuple
                        remote_windows[win_key] = GenomicWindow(
                            chrom=chrom_orig,
                            start=ens_start - 1,
                            end=ens_end,
                            sequence=sequence,
                        )
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - seq_fetch_start) * 1000)
                yield emit(
                    {
                        "type": "step",
                        "name": "Seq Fetch",
                        "status": "error",
                        "detail": str(exc),
                        "elapsed_ms": elapsed_ms,
                    }
                )
                yield emit({"type": "error", "error": str(exc)})
                return

            seq_fetch_elapsed_ms = int((time.perf_counter() - seq_fetch_start) * 1000)
            local_detail = ", ".join(seq_cache.keys())
            remote_detail = f" + {len(remote_chroms)} chrom(s) via Ensembl" if remote_chroms else ""
            seq_detail = (
                f"{local_detail}{remote_detail} in {_format_elapsed_ms(seq_fetch_elapsed_ms)}"
            )
            _log_step(
                "Seq Fetch",
                local_detail + remote_detail if local_detail or remote_detail else "complete",
                seq_fetch_elapsed_ms,
            )
            yield emit(
                {
                    "type": "step",
                    "name": "Seq Fetch",
                    "status": "success",
                    "detail": seq_detail,
                    "elapsed_ms": seq_fetch_elapsed_ms,
                }
            )
            await asyncio.sleep(0)

            orf_start = time.perf_counter()
            yield emit(
                {
                    "type": "running",
                    "name": "6-Frame ORF",
                    "detail": "Scanning all reading frames",
                    "elapsed_ms": 0,
                }
            )
            await asyncio.sleep(0)

            all_effects: list[FrameEffect] = []
            window_sequences: dict[str, str] = {}
            window_meta: dict[str, tuple[int, int]] = {}
            total_orfs = 0

            for variant in normalized:
                if variant.chrom in seq_cache:
                    window = window_mod.extract(variant, seq_cache[variant.chrom])
                else:
                    window = remote_windows[f"{variant.chrom}_{variant.pos}"]

                orfs = find_orfs(window.sequence, request.min_orf_length)
                total_orfs += len(orfs)
                effects = engine.reclassify(variant, orfs, window)

                window_size = len(window.sequence)
                variant_in_window = variant.pos - 1 - window.start
                window_key = f"{variant.gene}_{variant.pos}"
                window_sequences[window_key] = window.sequence
                window_meta[window_key] = (window_size, variant_in_window)

                for effect in effects:
                    effect.variant = variant
                all_effects.extend(effects)

            orf_elapsed_ms = int((time.perf_counter() - orf_start) * 1000)
            orf_detail = (
                f"{total_orfs} ORFs across {len(normalized)} variants in "
                f"{_format_elapsed_ms(orf_elapsed_ms)}"
            )
            _log_step(
                "6-Frame ORF",
                f"{total_orfs} ORFs across {len(normalized)} variants",
                orf_elapsed_ms,
            )
            yield emit(
                {
                    "type": "step",
                    "name": "6-Frame ORF",
                    "status": "success",
                    "detail": orf_detail,
                    "elapsed_ms": orf_elapsed_ms,
                }
            )
            await asyncio.sleep(0)

            reclassify_start = time.perf_counter()
            yield emit(
                {
                    "type": "running",
                    "name": "Reclassify",
                    "detail": "Summarizing frame effects",
                    "elapsed_ms": 0,
                }
            )
            await asyncio.sleep(0)

            result_summary = summary_mod.aggregate(all_effects)
            reclassified = sum(
                count for cls, count in result_summary.counts_by_type.items() if cls != "Silent"
            )
            frames_affected = len(
                {effect.orf.frame for effect in all_effects if effect.new_class != "Silent"}
            )
            reclassify_elapsed_ms = int((time.perf_counter() - reclassify_start) * 1000)
            reclassify_detail = (
                f"{reclassified} reclassified in {_format_elapsed_ms(reclassify_elapsed_ms)}"
            )
            _log_step("Reclassify", f"{reclassified} reclassified", reclassify_elapsed_ms)
            yield emit(
                {
                    "type": "step",
                    "name": "Reclassify",
                    "status": "success",
                    "detail": reclassify_detail,
                    "elapsed_ms": reclassify_elapsed_ms,
                }
            )
            await asyncio.sleep(0)

            def build_effect(effect: FrameEffect) -> dict:
                variant = effect.variant
                gene = variant.gene if variant else ""
                pos = variant.pos if variant else abs(effect.orf.pos)
                window_key = f"{gene}_{pos}"
                window_size, variant_in_window = window_meta.get(window_key, (1001, 500))
                return _effect_to_dict(effect, window_size, variant_in_window)

            yield emit(
                {
                    "type": "fast_complete",
                    "job_id": job_id,
                    "variants": [build_effect(effect) for effect in all_effects],
                    "summary": _build_fast_summary(
                        total_input_variants=len(all_variants),
                        total_silent_variants=len(silent),
                        total_orfs=total_orfs,
                        total_effects=len(all_effects),
                        reclassified_effects=reclassified,
                        frames_affected=frames_affected,
                    ),
                    "variant_windows": window_sequences,
                    "analysis_meta": analysis_meta,
                }
            )
            await asyncio.sleep(0)

            reclassified_effects = [
                effect for effect in all_effects if effect.new_class != "Silent"
            ]
            if reclassified_effects:
                fast_result = FastLaneResult(
                    summary=ReclassifySummary(),
                    sankey_data=[],
                    reclassified_variants=reclassified_effects,
                )
                loop = asyncio.get_running_loop()
                progress_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()
                running_name: str | None = None
                running_detail: str | None = None
                running_elapsed_ms = 0
                running_started_at: float | None = None
                running_progress_current: int | None = None
                running_progress_total: int | None = None

                def report_progress(event: dict[str, object]) -> None:
                    loop.call_soon_threadsafe(progress_queue.put_nowait, event)

                deep_lane_task = asyncio.create_task(
                    asyncio.to_thread(
                        deep_lane.run_streaming,
                        fast_result,
                        _DEFAULT_HLA_ALLELES,
                        report_progress,
                    )
                )

                while True:
                    if deep_lane_task.done() and progress_queue.empty():
                        break
                    try:
                        event = await asyncio.wait_for(progress_queue.get(), timeout=5.0)
                    except TimeoutError:
                        if running_name is not None:
                            heartbeat_elapsed_ms = running_elapsed_ms
                            if running_started_at is not None:
                                heartbeat_elapsed_ms = max(
                                    running_elapsed_ms,
                                    int((loop.time() - running_started_at) * 1000),
                                )
                            yield emit(
                                {
                                    "type": "running",
                                    "name": running_name,
                                    "detail": running_detail,
                                    "elapsed_ms": heartbeat_elapsed_ms,
                                    "progress_current": running_progress_current,
                                    "progress_total": running_progress_total,
                                }
                            )
                            await asyncio.sleep(0)
                        continue

                    event_type = event.get("type")
                    if event_type == "running":
                        running_name = _event_str(event, "name")
                        running_detail = _event_str(event, "detail")
                        running_elapsed_ms = _event_int(event, "elapsed_ms")
                        running_progress_current = _event_optional_int(
                            event,
                            "progress_current",
                        )
                        running_progress_total = _event_optional_int(
                            event,
                            "progress_total",
                        )
                        running_started_at = (
                            loop.time() - (running_elapsed_ms / 1000)
                            if running_name is not None
                            else None
                        )
                        yield emit(
                            {
                                "type": "running",
                                "name": running_name,
                                "detail": running_detail,
                                "elapsed_ms": running_elapsed_ms,
                                "progress_current": running_progress_current,
                                "progress_total": running_progress_total,
                            }
                        )
                        await asyncio.sleep(0)
                    elif event_type == "step":
                        step_name = _event_str(event, "name")
                        if running_name == step_name:
                            running_name = None
                            running_detail = None
                            running_elapsed_ms = 0
                            running_started_at = None
                            running_progress_current = None
                            running_progress_total = None
                        yield emit(
                            {
                                "type": "step",
                                "name": step_name,
                                "status": _event_str(event, "status"),
                                "detail": _event_str(event, "detail"),
                                "elapsed_ms": _event_int(event, "elapsed_ms"),
                            }
                        )
                        await asyncio.sleep(0)
                    elif event_type == "warning":
                        yield emit(
                            {
                                "type": "warning",
                                "provider": _event_str(event, "provider"),
                                "message": _event_str(event, "message"),
                                "variant_id": _event_str(event, "variant_id"),
                                "fatal": bool(event.get("fatal", False)),
                                "elapsed_ms": _event_int(event, "elapsed_ms"),
                            }
                        )
                        await asyncio.sleep(0)
                    elif event_type == "candidate_ready":
                        candidate = event.get("candidate")
                        if isinstance(candidate, ScoredCandidate):
                            yield emit(
                                _candidate_to_enrichment_event(
                                    candidate,
                                    _event_int(event, "elapsed_ms"),
                                )
                            )
                            await asyncio.sleep(0)

                try:
                    await deep_lane_task
                except Exception as exc:
                    yield emit(
                        {
                            "type": "step",
                            "name": running_name or "Domain & Evidence",
                            "status": "error",
                            "detail": str(exc),
                            "elapsed_ms": running_elapsed_ms,
                        }
                    )
                    yield emit({"type": "error", "error": str(exc)})
                    return
            else:
                for name in (
                    "Peptides",
                    "MHC Binding",
                    "Domain & Evidence",
                    "Rank & Score",
                ):
                    yield emit(
                        {
                            "type": "step",
                            "name": name,
                            "status": "skipped",
                            "detail": "0 reclassified variants",
                            "elapsed_ms": 0,
                        }
                    )
                    await asyncio.sleep(0)

            yield emit({"type": "complete"})
        except Exception as exc:
            yield emit({"type": "error", "error": str(exc)})
        finally:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    return StreamingResponse(generate(), media_type="application/x-ndjson")
