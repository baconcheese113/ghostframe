import json
from collections.abc import Callable
from typing import cast
from unittest.mock import patch

from fastapi.testclient import TestClient

from ghostframe.models import (
    ORF,
    BindingPrediction,
    DeepLaneResult,
    EvidenceLookupResult,
    FastLaneResult,
    FrameEffect,
    GenomicWindow,
    NormalizedVariant,
    Peptide,
    ReclassifySummary,
    ScoredCandidate,
    Variant,
)
from ghostframe_api.app import create_app


def _make_raw_variant(sample_barcode: str | None = None) -> Variant:
    return Variant(
        chrom="17",
        pos=7675994,
        ref="G",
        alt="T",
        classification="Silent",
        gene="TP53",
        sample_barcode=sample_barcode,
    )


def _normalize_variant(variant: Variant) -> NormalizedVariant:
    return NormalizedVariant(
        chrom=variant.chrom,
        pos=variant.pos,
        ref=variant.ref,
        alt=variant.alt,
        classification=variant.classification,
        gene=variant.gene,
    )


def _make_orf() -> ORF:
    return ORF(
        frame=1,
        pos=1,
        length=12,
        dna="ATGGCCGCCTAA",
    )


def _make_effect() -> FrameEffect:
    return FrameEffect(
        orf=_make_orf(),
        old_class="Silent",
        new_class="Missense",
        ref_aa="A",
        alt_aa="V",
        codon_pos=1,
    )


def _make_bound_candidate(effect: FrameEffect) -> ScoredCandidate:
    binding = BindingPrediction(
        peptide=Peptide(sequence="GILGFVFTL", start=0, k=9),
        allele="HLA-A*02:01",
        affinity=125.0,
        rank=1.5,
    )
    return ScoredCandidate(
        effect=effect,
        binding=binding,
        domain_hits=[],
        evidence=EvidenceLookupResult(tier=2),
        score=0.88,
    )


def _make_unbound_candidate(effect: FrameEffect) -> ScoredCandidate:
    return ScoredCandidate(
        effect=effect,
        binding=None,
        domain_hits=[],
        evidence=EvidenceLookupResult(tier=1),
        score=0.12,
    )


def _parse_events(payload: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in payload.splitlines() if line.strip()]


def test_analyze_streams_demo_metadata_warning_and_incremental_enrichment() -> None:
    app = create_app()
    client = TestClient(app)
    raw_variant = _make_raw_variant()
    normalized_variant = _normalize_variant(raw_variant)
    effect = _make_effect()
    window = GenomicWindow(chrom="17", start=0, end=12, sequence="ATGGCCGCCTAA")

    def fake_run_streaming(
        fast_result: FastLaneResult,
        _alleles: list[str],
        progress_callback: Callable[[dict[str, object]], None],
    ) -> DeepLaneResult:
        assert callable(progress_callback)
        effect_with_variant = fast_result.reclassified_variants[0]
        candidate = _make_bound_candidate(effect_with_variant)
        progress_callback(
            {
                "type": "running",
                "name": "Peptides",
                "detail": "Generating peptides for 1 variants",
                "elapsed_ms": 0,
            }
        )
        progress_callback(
            {
                "type": "step",
                "name": "Peptides",
                "status": "success",
                "detail": "4 peptides, 4 unique in 0.01s",
                "elapsed_ms": 10,
            }
        )
        progress_callback(
            {
                "type": "running",
                "name": "MHC Binding",
                "detail": "Predicting 4 unique peptides across 1 allele(s)",
                "elapsed_ms": 0,
            }
        )
        progress_callback(
            {
                "type": "step",
                "name": "MHC Binding",
                "status": "success",
                "detail": "1 best bindings in 0.02s",
                "elapsed_ms": 20,
            }
        )
        progress_callback(
            {
                "type": "running",
                "name": "Domain & Evidence",
                "detail": "ClinVar 0/1 in 0.03s",
                "elapsed_ms": 30,
                "progress_current": 0,
                "progress_total": 4,
            }
        )
        progress_callback(
            {
                "type": "warning",
                "provider": "clinvar",
                "message": "ClinVar rate-limited the request; continuing without ClinVar evidence.",
                "variant_id": None,
                "fatal": False,
                "elapsed_ms": 35,
            }
        )
        progress_callback(
            {
                "type": "candidate_ready",
                "candidate": candidate,
                "variant_id": "TP53_1_7675994",
                "elapsed_ms": 40,
            }
        )
        progress_callback(
            {
                "type": "step",
                "name": "Domain & Evidence",
                "status": "success",
                "detail": "1/1 variants enriched in 0.04s",
                "elapsed_ms": 40,
            }
        )
        progress_callback(
            {
                "type": "running",
                "name": "Rank & Score",
                "detail": "Ranking 1 candidates",
                "elapsed_ms": 0,
            }
        )
        progress_callback(
            {
                "type": "step",
                "name": "Rank & Score",
                "status": "success",
                "detail": "1 candidates ranked in 0.01s",
                "elapsed_ms": 10,
            }
        )
        return DeepLaneResult(
            peptides=[candidate.binding.peptide] if candidate.binding else [],
            binding_predictions=[candidate.binding] if candidate.binding else [],
            evidence=candidate.evidence,
            domain_hits=[],
            ranked_candidates=[candidate],
        )

    with (
        patch("ghostframe_api.routes.analysis.maf.parse", return_value=[raw_variant]),
        patch("ghostframe_api.routes.analysis.filters.keep_silent", return_value=[raw_variant]),
        patch(
            "ghostframe_api.routes.analysis.normalize.normalize",
            side_effect=lambda variant: normalized_variant,
        ),
        patch("ghostframe_api.routes.analysis.local.fetch", return_value=window.sequence),
        patch("ghostframe_api.routes.analysis.window_mod.extract", return_value=window),
        patch("ghostframe_api.routes.analysis.find_orfs", return_value=[_make_orf()]),
        patch("ghostframe_api.routes.analysis.engine.reclassify", return_value=[effect]),
        patch(
            "ghostframe_api.routes.analysis.summary_mod.aggregate",
            return_value=ReclassifySummary(counts_by_type={"Missense": 1}),
        ),
        patch(
            "ghostframe_api.routes.analysis.deep_lane.run_streaming",
            side_effect=fake_run_streaming,
        ),
    ):
        response = client.post("/api/analyze", json={"maf_content": None})

    assert response.status_code == 200
    events = _parse_events(response.text)
    event_types = [event["type"] for event in events]
    deep_step_names = [
        event.get("name") for event in events if event["type"] in {"running", "step"}
    ]
    fast_complete_event = next(event for event in events if event["type"] == "fast_complete")

    assert event_types.index("fast_complete") < event_types.index("warning")
    assert event_types.index("enrich_complete") < event_types.index("complete")
    assert "Domain & Evidence" in deep_step_names
    assert "Deep Lane" not in deep_step_names
    assert fast_complete_event["summary"] == {
        "total_input_variants": 1,
        "total_silent_variants": 1,
        "total_orfs": 1,
        "total_effects": 1,
        "reclassified_effects": 1,
        "total_silent": 1,
        "reclassified": 1,
        "frames_affected": 1,
        "best_ic50": None,
    }
    assert fast_complete_event["analysis_meta"] == {
        "primary_label": "Demo dataset",
        "secondary_label": "1 variant",
        "sample_count": 0,
        "variant_count": 1,
        "is_demo": True,
        "hla_alleles": ["HLA-A*02:01"],
    }
    domain_running_event = next(
        event
        for event in events
        if event["type"] == "running" and event.get("name") == "Domain & Evidence"
    )
    assert domain_running_event["progress_current"] == 0
    assert domain_running_event["progress_total"] == 4
    assert any(
        event["type"] == "warning" and event.get("provider") == "clinvar" for event in events
    )


def test_analyze_serializes_missing_binding_as_null_and_uses_sample_barcode_label() -> None:
    app = create_app()
    client = TestClient(app)
    raw_variant = _make_raw_variant(sample_barcode="SAMPLE-01")
    normalized_variant = _normalize_variant(raw_variant)
    effect = _make_effect()
    window = GenomicWindow(chrom="17", start=0, end=12, sequence="ATGGCCGCCTAA")

    def fake_run_streaming(
        fast_result: FastLaneResult,
        _alleles: list[str],
        progress_callback: Callable[[dict[str, object]], None],
    ) -> DeepLaneResult:
        assert callable(progress_callback)
        effect_with_variant = fast_result.reclassified_variants[0]
        candidate = _make_unbound_candidate(effect_with_variant)
        progress_callback(
            {
                "type": "candidate_ready",
                "candidate": candidate,
                "variant_id": "TP53_1_7675994",
                "elapsed_ms": 12,
            }
        )
        return DeepLaneResult(
            peptides=[],
            binding_predictions=[],
            evidence=candidate.evidence,
            domain_hits=[],
            ranked_candidates=[candidate],
        )

    with (
        patch("ghostframe_api.routes.analysis.maf.parse", return_value=[raw_variant]),
        patch("ghostframe_api.routes.analysis.filters.keep_silent", return_value=[raw_variant]),
        patch(
            "ghostframe_api.routes.analysis.normalize.normalize",
            side_effect=lambda variant: normalized_variant,
        ),
        patch("ghostframe_api.routes.analysis.local.fetch", return_value=window.sequence),
        patch("ghostframe_api.routes.analysis.window_mod.extract", return_value=window),
        patch("ghostframe_api.routes.analysis.find_orfs", return_value=[_make_orf()]),
        patch("ghostframe_api.routes.analysis.engine.reclassify", return_value=[effect]),
        patch(
            "ghostframe_api.routes.analysis.summary_mod.aggregate",
            return_value=ReclassifySummary(counts_by_type={"Missense": 1}),
        ),
        patch(
            "ghostframe_api.routes.analysis.deep_lane.run_streaming",
            side_effect=fake_run_streaming,
        ),
    ):
        response = client.post(
            "/api/analyze",
            json={"maf_content": "mock maf", "maf_filename": "cohort.maf"},
        )

    assert response.status_code == 200
    events = _parse_events(response.text)
    fast_complete_event = next(event for event in events if event["type"] == "fast_complete")
    enrich_complete_event = next(event for event in events if event["type"] == "enrich_complete")
    candidates = cast(list[dict[str, object]], enrich_complete_event["candidates"])
    candidate = candidates[0]

    assert fast_complete_event["analysis_meta"] == {
        "primary_label": "SAMPLE-01",
        "secondary_label": "cohort.maf",
        "sample_count": 1,
        "variant_count": 1,
        "is_demo": False,
        "hla_alleles": ["HLA-A*02:01"],
    }
    assert candidate["peptide_sequence"] is None
    assert candidate["allele"] is None
    assert candidate["ic50"] is None
    assert candidate["rank"] is None


def test_analyze_falls_back_to_filename_for_multi_sample_uploads() -> None:
    app = create_app()
    client = TestClient(app)
    raw_variants = [
        _make_raw_variant(sample_barcode="SAMPLE-A"),
        Variant(
            chrom="17",
            pos=7676000,
            ref="C",
            alt="A",
            classification="Silent",
            gene="TP53",
            sample_barcode="SAMPLE-B",
        ),
    ]
    normalized_variants = [_normalize_variant(variant) for variant in raw_variants]
    window = GenomicWindow(chrom="17", start=0, end=12, sequence="ATGGCCGCCTAA")

    with (
        patch("ghostframe_api.routes.analysis.maf.parse", return_value=raw_variants),
        patch("ghostframe_api.routes.analysis.filters.keep_silent", return_value=raw_variants),
        patch(
            "ghostframe_api.routes.analysis.normalize.normalize",
            side_effect=normalized_variants,
        ),
        patch("ghostframe_api.routes.analysis.local.fetch", return_value=window.sequence),
        patch("ghostframe_api.routes.analysis.window_mod.extract", return_value=window),
        patch("ghostframe_api.routes.analysis.find_orfs", return_value=[_make_orf()]),
        patch("ghostframe_api.routes.analysis.engine.reclassify", return_value=[]),
        patch(
            "ghostframe_api.routes.analysis.summary_mod.aggregate",
            return_value=ReclassifySummary(counts_by_type={"Silent": 2}),
        ),
    ):
        response = client.post(
            "/api/analyze",
            json={"maf_content": "mock maf", "maf_filename": "cohort.maf"},
        )

    assert response.status_code == 200
    events = _parse_events(response.text)
    fast_complete_event = next(event for event in events if event["type"] == "fast_complete")

    assert fast_complete_event["analysis_meta"] == {
        "primary_label": "cohort.maf",
        "secondary_label": "2 samples / 2 variants",
        "sample_count": 2,
        "variant_count": 2,
        "is_demo": False,
        "hla_alleles": ["HLA-A*02:01"],
    }
