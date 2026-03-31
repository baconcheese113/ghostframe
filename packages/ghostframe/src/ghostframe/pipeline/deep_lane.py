"""Deep lane pipeline: batched enrichment for reclassified variants.

peptide generation -> MHC binding prediction -> domain annotation ->
external evidence linking -> candidate scoring -> ranking.
"""

import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from hashlib import sha256
from typing import cast

from cachetools import TTLCache

from ghostframe.domain import hmmer
from ghostframe.evidence import clinvar, openprot, synmicdb
from ghostframe.mhc.mhcflurry import MHCflurryPredictor
from ghostframe.models import (
    BindingPrediction,
    ClinVarHit,
    DeepLaneResult,
    DomainHit,
    EvidenceLookupResult,
    FastLaneResult,
    FrameEffect,
    NormalizedVariant,
    OpenProtHit,
    Peptide,
    ScoredCandidate,
    SynMICdbHit,
)
from ghostframe.orfs.sequence import translate
from ghostframe.peptides.generator import sliding_kmers
from ghostframe.ranking import ranker, scorer

_DEFAULT_ALLELES = ["HLA-A*02:01"]
_CACHE_TTL_SECONDS = 24 * 60 * 60
_HMMER_MAX_WORKERS = 20
_OPENPROT_MAX_WORKERS = 5
_CLINVAR_MAX_WORKERS = 3
_SYNMICDB_MAX_WORKERS = 20
_PROGRESS_REPORT_EVERY = 25
_PROVIDER_LABELS = {
    "hmmer": "HMMER",
    "openprot": "OpenProt",
    "clinvar": "ClinVar",
    "synmicdb": "SynMICdb",
}

type _ProteinKey = str
type _GeneKey = str
type _VariantKey = tuple[str, int, str, str, str]
type _ProviderKey = _ProteinKey | _GeneKey | _VariantKey
type _ProgressEvent = dict[str, object]
type _ProgressCallback = Callable[[_ProgressEvent], None]


@dataclass(frozen=True)
class _EffectContext:
    index: int
    effect: FrameEffect
    protein_key: _ProteinKey
    gene_key: _GeneKey | None
    variant_key: _VariantKey | None
    best_binding: BindingPrediction | None


@dataclass(frozen=True)
class _FutureMeta:
    provider: str
    key: _ProviderKey


@dataclass
class _ProviderOutcome[T]:
    value: T
    warnings: list[str] = field(default_factory=list)
    cacheable: bool = True


_HMMER_CACHE: TTLCache[_ProteinKey, list[DomainHit]] = TTLCache(
    maxsize=4096,
    ttl=_CACHE_TTL_SECONDS,
)
_OPENPROT_CACHE: TTLCache[_GeneKey, OpenProtHit | None] = TTLCache(
    maxsize=4096,
    ttl=_CACHE_TTL_SECONDS,
)


def run(
    fast_result: FastLaneResult,
    hla_alleles: list[str] | None = None,
    progress_callback: _ProgressCallback | None = None,
) -> DeepLaneResult:
    """Batch wrapper around the streaming deep-lane implementation."""
    return run_streaming(
        fast_result,
        hla_alleles=hla_alleles,
        progress_callback=progress_callback,
    )


def run_streaming(
    fast_result: FastLaneResult,
    hla_alleles: list[str] | None = None,
    progress_callback: _ProgressCallback | None = None,
) -> DeepLaneResult:
    """Run deep analysis and emit structured progress events while it works."""
    effects = fast_result.reclassified_variants
    if not effects:
        return DeepLaneResult(
            peptides=[],
            binding_predictions=[],
            evidence=None,
            domain_hits=[],
            ranked_candidates=[],
        )

    total_start = time.perf_counter()
    alleles = hla_alleles or _DEFAULT_ALLELES
    predictor = MHCflurryPredictor()

    all_peptides: list[Peptide] = []
    peptide_sets: list[list[Peptide]] = []
    unique_peptides: dict[str, Peptide] = {}
    proteins: list[str] = []
    protein_keys: list[_ProteinKey] = []

    peptides_start = time.perf_counter()
    _emit_running(
        progress_callback,
        "Peptides",
        f"Generating peptides for {len(effects)} variants",
        0,
    )
    for effect in effects:
        protein = translate(effect.orf.dna)
        proteins.append(protein)
        protein_keys.append(_protein_cache_key(protein))

        peptides = (
            sliding_kmers(protein, effect.codon_pos)
            if effect.codon_pos is not None
            else _all_kmers(protein)
        )
        peptide_sets.append(peptides)
        all_peptides.extend(peptides)
        for peptide in peptides:
            unique_peptides.setdefault(peptide.sequence, peptide)

    peptides_elapsed_ms = _elapsed_ms(peptides_start)
    print(
        "[deep_lane] peptides "
        f"({len(effects)} variants, {len(all_peptides)} peptides, "
        f"{len(unique_peptides)} unique): {_format_elapsed_ms(peptides_elapsed_ms)}"
    )
    _emit_step(
        progress_callback,
        "Peptides",
        "success",
        (
            f"{len(all_peptides)} peptides, {len(unique_peptides)} unique "
            f"in {_format_elapsed_ms(peptides_elapsed_ms)}"
        ),
        peptides_elapsed_ms,
    )

    mhc_start = time.perf_counter()
    _emit_running(
        progress_callback,
        "MHC Binding",
        (f"Predicting {len(unique_peptides)} unique peptides across {len(alleles)} allele(s)"),
        0,
    )
    prediction_by_sequence = _predict_bindings(
        predictor,
        unique_peptides.values(),
        alleles,
    )
    best_bindings = [
        _best_binding_for_peptides(peptides, prediction_by_sequence) for peptides in peptide_sets
    ]
    mhc_elapsed_ms = _elapsed_ms(mhc_start)
    binding_predictions = [binding for binding in best_bindings if binding is not None]
    print(
        "[deep_lane] mhc binding "
        f"({len(unique_peptides)} unique peptides, {len(alleles)} allele(s), "
        f"{len(binding_predictions)} best bindings): {_format_elapsed_ms(mhc_elapsed_ms)}"
    )
    _emit_step(
        progress_callback,
        "MHC Binding",
        "success",
        (f"{len(binding_predictions)} best bindings in {_format_elapsed_ms(mhc_elapsed_ms)}"),
        mhc_elapsed_ms,
    )

    effect_contexts, protein_dependents, gene_dependents, variant_dependents = (
        _build_effect_contexts(
            effects,
            protein_keys,
            best_bindings,
        )
    )

    domain_by_protein_key: dict[_ProteinKey, list[DomainHit]] = {}
    proteins_to_submit: dict[_ProteinKey, str] = {}
    for protein_key, protein in zip(protein_keys, proteins, strict=True):
        if protein_key in domain_by_protein_key:
            continue
        cached_hits = _HMMER_CACHE.get(protein_key)
        if cached_hits is not None:
            domain_by_protein_key[protein_key] = cached_hits
            continue
        proteins_to_submit[protein_key] = protein

    openprot_by_gene: dict[_GeneKey, OpenProtHit | None] = {}
    genes_to_submit: dict[_GeneKey, FrameEffect] = {}
    synmicdb_by_variant: dict[_VariantKey, SynMICdbHit | None] = {}
    clinvar_by_variant: dict[_VariantKey, ClinVarHit | None] = {}
    variants_to_submit: dict[_VariantKey, NormalizedVariant] = {}

    for ctx in effect_contexts:
        if ctx.variant_key is not None and ctx.effect.variant is not None:
            variants_to_submit.setdefault(ctx.variant_key, ctx.effect.variant)

        if ctx.gene_key is None or ctx.effect.variant is None:
            continue

        if ctx.gene_key in openprot_by_gene:
            continue

        cached_hit = _OPENPROT_CACHE.get(ctx.gene_key)
        if cached_hit is not None or ctx.gene_key in _OPENPROT_CACHE:
            openprot_by_gene[ctx.gene_key] = cached_hit
        else:
            genes_to_submit.setdefault(ctx.gene_key, ctx.effect)

    provider_totals = {
        "hmmer": len(domain_by_protein_key) + len(proteins_to_submit),
        "openprot": len(openprot_by_gene) + len(genes_to_submit),
        "clinvar": len(variants_to_submit),
        "synmicdb": len(variants_to_submit),
    }
    provider_completed = {
        "hmmer": len(domain_by_protein_key),
        "openprot": len(openprot_by_gene),
        "clinvar": 0,
        "synmicdb": 0,
    }

    phase2_start = time.perf_counter()
    phase2_detail = _phase2_detail(provider_completed, provider_totals, 0)
    phase2_progress_current, phase2_progress_total = _phase2_progress(
        provider_completed,
        provider_totals,
    )
    print(
        "[deep_lane] domain & evidence queued "
        f"hmmer={provider_completed['hmmer']}/{provider_totals['hmmer']} cached, "
        f"openprot={provider_completed['openprot']}/{provider_totals['openprot']} cached, "
        f"clinvar={provider_totals['clinvar']}, synmicdb={provider_totals['synmicdb']}"
    )
    _emit_running(
        progress_callback,
        "Domain & Evidence",
        phase2_detail,
        0,
        progress_current=phase2_progress_current,
        progress_total=phase2_progress_total,
    )

    candidate_by_index: dict[int, ScoredCandidate] = {}
    _maybe_emit_ready_candidates(
        range(len(effect_contexts)),
        effect_contexts,
        domain_by_protein_key,
        openprot_by_gene,
        synmicdb_by_variant,
        clinvar_by_variant,
        candidate_by_index,
        progress_callback,
        _elapsed_ms(total_start),
    )

    future_to_meta: dict[Future[object], _FutureMeta] = {}
    provider_started_at = {
        "hmmer": time.perf_counter(),
        "openprot": time.perf_counter(),
        "clinvar": time.perf_counter(),
        "synmicdb": time.perf_counter(),
    }

    with (
        ThreadPoolExecutor(max_workers=_HMMER_MAX_WORKERS) as hmmer_pool,
        ThreadPoolExecutor(max_workers=_OPENPROT_MAX_WORKERS) as openprot_pool,
        ThreadPoolExecutor(max_workers=_CLINVAR_MAX_WORKERS) as clinvar_pool,
        ThreadPoolExecutor(max_workers=_SYNMICDB_MAX_WORKERS) as synmicdb_pool,
    ):
        for protein_key, protein in proteins_to_submit.items():
            future_to_meta[cast(Future[object], hmmer_pool.submit(_safe_hmmer_scan, protein))] = (
                _FutureMeta("hmmer", protein_key)
            )
        for gene_key, effect in genes_to_submit.items():
            if effect.variant is None:
                continue
            future_to_meta[
                cast(
                    Future[object],
                    openprot_pool.submit(
                        _safe_openprot_lookup,
                        effect,
                    ),
                )
            ] = _FutureMeta("openprot", gene_key)
        for variant_key, variant in variants_to_submit.items():
            future_to_meta[
                cast(Future[object], clinvar_pool.submit(_safe_clinvar_lookup, variant))
            ] = _FutureMeta("clinvar", variant_key)
            future_to_meta[
                cast(Future[object], synmicdb_pool.submit(_safe_synmicdb_lookup, variant))
            ] = _FutureMeta("synmicdb", variant_key)

        for future in as_completed(future_to_meta):
            meta = future_to_meta[future]
            try:
                outcome = cast(_ProviderOutcome[object], future.result())
            except Exception as exc:
                outcome = _fallback_outcome(meta.provider, exc)

            provider_completed[meta.provider] += 1
            _store_provider_outcome(
                meta,
                outcome,
                domain_by_protein_key,
                openprot_by_gene,
                synmicdb_by_variant,
                clinvar_by_variant,
            )
            for warning in outcome.warnings:
                _emit_warning(
                    progress_callback,
                    meta.provider,
                    warning,
                    None,
                    _elapsed_ms(total_start),
                )

            affected_indices = _affected_effect_indices(
                meta,
                protein_dependents,
                gene_dependents,
                variant_dependents,
            )
            _maybe_emit_ready_candidates(
                affected_indices,
                effect_contexts,
                domain_by_protein_key,
                openprot_by_gene,
                synmicdb_by_variant,
                clinvar_by_variant,
                candidate_by_index,
                progress_callback,
                _elapsed_ms(total_start),
            )

            current_completed = provider_completed[meta.provider]
            current_total = provider_totals[meta.provider]
            if current_total > 0 and (
                current_completed == current_total
                or current_completed == 1
                or current_completed % _PROGRESS_REPORT_EVERY == 0
            ):
                provider_elapsed_ms = _elapsed_ms(provider_started_at[meta.provider])
                print(
                    "[deep_lane] domain & evidence "
                    f"{meta.provider}: {current_completed}/{current_total} "
                    f"({_format_elapsed_ms(provider_elapsed_ms)})"
                )

            phase2_elapsed_ms = _elapsed_ms(phase2_start)
            phase2_progress_current, phase2_progress_total = _phase2_progress(
                provider_completed,
                provider_totals,
            )
            _emit_running(
                progress_callback,
                "Domain & Evidence",
                _phase2_detail(provider_completed, provider_totals, phase2_elapsed_ms),
                phase2_elapsed_ms,
                progress_current=phase2_progress_current,
                progress_total=phase2_progress_total,
            )

    _maybe_emit_ready_candidates(
        range(len(effect_contexts)),
        effect_contexts,
        domain_by_protein_key,
        openprot_by_gene,
        synmicdb_by_variant,
        clinvar_by_variant,
        candidate_by_index,
        progress_callback,
        _elapsed_ms(total_start),
    )

    phase2_elapsed_ms = _elapsed_ms(phase2_start)
    print(
        "[deep_lane] domain & evidence complete "
        f"({len(candidate_by_index)}/{len(effect_contexts)} variants): "
        f"{_format_elapsed_ms(phase2_elapsed_ms)}"
    )
    _emit_step(
        progress_callback,
        "Domain & Evidence",
        "success",
        (
            f"{len(candidate_by_index)}/{len(effect_contexts)} variants enriched in "
            f"{_format_elapsed_ms(phase2_elapsed_ms)}"
        ),
        phase2_elapsed_ms,
    )

    phase3_start = time.perf_counter()
    _emit_running(
        progress_callback,
        "Rank & Score",
        f"Ranking {len(candidate_by_index)} candidates",
        0,
    )
    ranked = ranker.rank(list(candidate_by_index.values()))
    phase3_elapsed_ms = _elapsed_ms(phase3_start)
    print(
        "[deep_lane] rank & score "
        f"({len(ranked)} candidates): {_format_elapsed_ms(phase3_elapsed_ms)}"
    )
    _emit_step(
        progress_callback,
        "Rank & Score",
        "success",
        f"{len(ranked)} candidates ranked in {_format_elapsed_ms(phase3_elapsed_ms)}",
        phase3_elapsed_ms,
    )

    total_elapsed_ms = _elapsed_ms(total_start)
    print(f"[deep_lane] total ({len(effects)} variants): {_format_elapsed_ms(total_elapsed_ms)}")
    _report(
        progress_callback,
        {
            "type": "deep_complete",
            "variants": len(effects),
            "candidates": len(ranked),
            "elapsed_ms": total_elapsed_ms,
        },
    )

    return DeepLaneResult(
        peptides=all_peptides,
        binding_predictions=binding_predictions,
        evidence=ranked[0].evidence if ranked else None,
        domain_hits=[hit for candidate in ranked for hit in candidate.domain_hits],
        ranked_candidates=ranked,
    )


def _predict_bindings(
    predictor: MHCflurryPredictor,
    peptides: Iterable[Peptide],
    alleles: list[str],
) -> dict[str, BindingPrediction]:
    peptide_list = list(peptides)
    if not peptide_list:
        return {}
    return {
        prediction.peptide.sequence: prediction
        for prediction in predictor.predict(peptide_list, alleles)
    }


def _best_binding_for_peptides(
    peptides: list[Peptide],
    prediction_by_sequence: dict[str, BindingPrediction],
) -> BindingPrediction | None:
    bindings = [
        BindingPrediction(
            peptide=peptide,
            allele=prediction.allele,
            affinity=prediction.affinity,
            rank=prediction.rank,
        )
        for peptide in peptides
        for prediction in [prediction_by_sequence.get(peptide.sequence)]
        if prediction is not None
    ]
    return min(bindings, key=lambda binding: binding.rank) if bindings else None


def _build_effect_contexts(
    effects: list[FrameEffect],
    protein_keys: list[_ProteinKey],
    best_bindings: list[BindingPrediction | None],
) -> tuple[
    list[_EffectContext],
    dict[_ProteinKey, set[int]],
    dict[_GeneKey, set[int]],
    dict[_VariantKey, set[int]],
]:
    effect_contexts: list[_EffectContext] = []
    protein_dependents: dict[_ProteinKey, set[int]] = defaultdict(set)
    gene_dependents: dict[_GeneKey, set[int]] = defaultdict(set)
    variant_dependents: dict[_VariantKey, set[int]] = defaultdict(set)

    for index, (effect, protein_key, best_binding) in enumerate(
        zip(effects, protein_keys, best_bindings, strict=True)
    ):
        gene_key: _GeneKey | None = None
        variant_key: _VariantKey | None = None
        if effect.variant is not None:
            variant_key = _variant_key(effect.variant)
            gene_key = _gene_cache_key(effect.variant.gene) or None

        ctx = _EffectContext(
            index=index,
            effect=effect,
            protein_key=protein_key,
            gene_key=gene_key,
            variant_key=variant_key,
            best_binding=best_binding,
        )
        effect_contexts.append(ctx)
        protein_dependents[protein_key].add(index)
        if gene_key is not None:
            gene_dependents[gene_key].add(index)
        if variant_key is not None:
            variant_dependents[variant_key].add(index)

    return (
        effect_contexts,
        protein_dependents,
        gene_dependents,
        variant_dependents,
    )


def _maybe_emit_ready_candidates(
    candidate_indices: Iterable[int],
    effect_contexts: list[_EffectContext],
    domain_by_protein_key: dict[_ProteinKey, list[DomainHit]],
    openprot_by_gene: dict[_GeneKey, OpenProtHit | None],
    synmicdb_by_variant: dict[_VariantKey, SynMICdbHit | None],
    clinvar_by_variant: dict[_VariantKey, ClinVarHit | None],
    candidate_by_index: dict[int, ScoredCandidate],
    progress_callback: _ProgressCallback | None,
    elapsed_ms: int,
) -> None:
    for index in candidate_indices:
        if index in candidate_by_index:
            continue

        ctx = effect_contexts[index]
        if not _is_effect_ready(
            ctx,
            domain_by_protein_key,
            openprot_by_gene,
            synmicdb_by_variant,
            clinvar_by_variant,
        ):
            continue

        candidate = _score_candidate(
            ctx,
            domain_by_protein_key,
            openprot_by_gene,
            synmicdb_by_variant,
            clinvar_by_variant,
        )
        candidate_by_index[index] = candidate
        _emit_candidate_ready(
            progress_callback,
            candidate,
            elapsed_ms,
        )


def _is_effect_ready(
    ctx: _EffectContext,
    domain_by_protein_key: dict[_ProteinKey, list[DomainHit]],
    openprot_by_gene: dict[_GeneKey, OpenProtHit | None],
    synmicdb_by_variant: dict[_VariantKey, SynMICdbHit | None],
    clinvar_by_variant: dict[_VariantKey, ClinVarHit | None],
) -> bool:
    if ctx.protein_key not in domain_by_protein_key:
        return False
    if ctx.gene_key is not None and ctx.gene_key not in openprot_by_gene:
        return False
    if ctx.variant_key is not None:
        if ctx.variant_key not in synmicdb_by_variant:
            return False
        if ctx.variant_key not in clinvar_by_variant:
            return False
    return True


def _score_candidate(
    ctx: _EffectContext,
    domain_by_protein_key: dict[_ProteinKey, list[DomainHit]],
    openprot_by_gene: dict[_GeneKey, OpenProtHit | None],
    synmicdb_by_variant: dict[_VariantKey, SynMICdbHit | None],
    clinvar_by_variant: dict[_VariantKey, ClinVarHit | None],
) -> ScoredCandidate:
    domain_hits = domain_by_protein_key.get(ctx.protein_key, [])
    openprot_hit = openprot_by_gene.get(ctx.gene_key) if ctx.gene_key is not None else None
    synmicdb_hit = synmicdb_by_variant.get(ctx.variant_key) if ctx.variant_key is not None else None
    clinvar_hit = clinvar_by_variant.get(ctx.variant_key) if ctx.variant_key is not None else None

    tier = 3 if synmicdb_hit else (2 if openprot_hit else 1)
    evidence = EvidenceLookupResult(
        openprot=openprot_hit,
        synmicdb=synmicdb_hit,
        clinvar=clinvar_hit,
        tier=tier,
    )

    score = scorer.score(ctx.effect, ctx.best_binding, domain_hits, evidence)
    return ScoredCandidate(
        effect=ctx.effect,
        binding=ctx.best_binding,
        domain_hits=domain_hits,
        evidence=evidence,
        score=score,
    )


def _safe_hmmer_scan(protein: str) -> _ProviderOutcome[list[DomainHit]]:
    try:
        return _ProviderOutcome(hmmer.scan(protein))
    except Exception as exc:
        return _ProviderOutcome(
            [],
            warnings=[
                (
                    f"HMMER lookup failed ({exc.__class__.__name__}); "
                    "continuing without domain evidence."
                )
            ],
            cacheable=False,
        )


def _safe_openprot_lookup(effect: FrameEffect) -> _ProviderOutcome[OpenProtHit | None]:
    try:
        if effect.variant is None:
            return _ProviderOutcome(None)
        return _ProviderOutcome(openprot.lookup(effect.orf, effect.variant.gene))
    except Exception as exc:
        return _ProviderOutcome(
            None,
            warnings=[
                (
                    f"OpenProt lookup failed ({exc.__class__.__name__}); "
                    "continuing without OpenProt evidence."
                )
            ],
            cacheable=False,
        )


def _safe_clinvar_lookup(
    variant: NormalizedVariant,
) -> _ProviderOutcome[ClinVarHit | None]:
    warnings: list[str] = []
    try:
        hit = clinvar.lookup(variant, warning_callback=warnings.append)
        return _ProviderOutcome(hit, warnings=warnings)
    except Exception as exc:
        return _ProviderOutcome(
            None,
            warnings=[
                *warnings,
                (
                    f"ClinVar lookup failed ({exc.__class__.__name__}); "
                    "continuing without ClinVar evidence."
                ),
            ],
            cacheable=False,
        )


def _safe_synmicdb_lookup(
    variant: NormalizedVariant,
) -> _ProviderOutcome[SynMICdbHit | None]:
    try:
        return _ProviderOutcome(synmicdb.lookup(variant))
    except Exception as exc:
        return _ProviderOutcome(
            None,
            warnings=[
                (
                    f"SynMICdb lookup failed ({exc.__class__.__name__}); "
                    "continuing without SynMICdb evidence."
                )
            ],
            cacheable=False,
        )


def _fallback_outcome(provider: str, exc: Exception) -> _ProviderOutcome[object]:
    provider_label = _PROVIDER_LABELS.get(provider, provider)
    fallback_value: object = [] if provider == "hmmer" else None
    return _ProviderOutcome(
        fallback_value,
        warnings=[
            (
                f"{provider_label} lookup failed ({exc.__class__.__name__}); "
                "continuing with partial evidence."
            )
        ],
        cacheable=False,
    )


def _store_provider_outcome(
    meta: _FutureMeta,
    outcome: _ProviderOutcome[object],
    domain_by_protein_key: dict[_ProteinKey, list[DomainHit]],
    openprot_by_gene: dict[_GeneKey, OpenProtHit | None],
    synmicdb_by_variant: dict[_VariantKey, SynMICdbHit | None],
    clinvar_by_variant: dict[_VariantKey, ClinVarHit | None],
) -> None:
    if meta.provider == "hmmer":
        protein_key = meta.key
        assert isinstance(protein_key, str)
        hits = outcome.value if isinstance(outcome.value, list) else []
        if outcome.cacheable:
            _HMMER_CACHE[protein_key] = hits
        domain_by_protein_key[protein_key] = hits
        return

    if meta.provider == "openprot":
        gene_key = meta.key
        assert isinstance(gene_key, str)
        hit = outcome.value if isinstance(outcome.value, OpenProtHit) else None
        if outcome.cacheable:
            _OPENPROT_CACHE[gene_key] = hit
        openprot_by_gene[gene_key] = hit
        return

    variant_key = meta.key
    assert isinstance(variant_key, tuple)
    if meta.provider == "synmicdb":
        synmicdb_by_variant[variant_key] = (
            outcome.value if isinstance(outcome.value, SynMICdbHit) else None
        )
        return

    clinvar_by_variant[variant_key] = (
        outcome.value if isinstance(outcome.value, ClinVarHit) else None
    )


def _affected_effect_indices(
    meta: _FutureMeta,
    protein_dependents: dict[_ProteinKey, set[int]],
    gene_dependents: dict[_GeneKey, set[int]],
    variant_dependents: dict[_VariantKey, set[int]],
) -> set[int]:
    if meta.provider == "hmmer":
        protein_key = meta.key
        assert isinstance(protein_key, str)
        return protein_dependents.get(protein_key, set())

    if meta.provider == "openprot":
        gene_key = meta.key
        assert isinstance(gene_key, str)
        return gene_dependents.get(gene_key, set())

    variant_key = meta.key
    assert isinstance(variant_key, tuple)
    return variant_dependents.get(variant_key, set())


def _emit_running(
    progress_callback: _ProgressCallback | None,
    name: str,
    detail: str,
    elapsed_ms: int,
    *,
    progress_current: int | None = None,
    progress_total: int | None = None,
) -> None:
    _report(
        progress_callback,
        {
            "type": "running",
            "name": name,
            "detail": detail,
            "elapsed_ms": elapsed_ms,
            "progress_current": progress_current,
            "progress_total": progress_total,
        },
    )


def _emit_step(
    progress_callback: _ProgressCallback | None,
    name: str,
    status: str,
    detail: str,
    elapsed_ms: int,
) -> None:
    _report(
        progress_callback,
        {
            "type": "step",
            "name": name,
            "status": status,
            "detail": detail,
            "elapsed_ms": elapsed_ms,
        },
    )


def _emit_warning(
    progress_callback: _ProgressCallback | None,
    provider: str,
    message: str,
    variant_id: str | None,
    elapsed_ms: int,
) -> None:
    print(f"[deep_lane] warning {provider}: {message}")
    _report(
        progress_callback,
        {
            "type": "warning",
            "provider": provider,
            "message": message,
            "variant_id": variant_id,
            "fatal": False,
            "elapsed_ms": elapsed_ms,
        },
    )


def _emit_candidate_ready(
    progress_callback: _ProgressCallback | None,
    candidate: ScoredCandidate,
    elapsed_ms: int,
) -> None:
    _report(
        progress_callback,
        {
            "type": "candidate_ready",
            "candidate": candidate,
            "variant_id": _candidate_variant_id(candidate.effect),
            "elapsed_ms": elapsed_ms,
        },
    )


def _report(
    progress_callback: _ProgressCallback | None,
    event: _ProgressEvent,
) -> None:
    if progress_callback is not None:
        progress_callback(event)


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _format_elapsed_ms(elapsed_ms: int) -> str:
    if elapsed_ms >= 60_000:
        minutes, remainder = divmod(elapsed_ms, 60_000)
        return f"{minutes}m {remainder / 1000:.1f}s"
    return f"{elapsed_ms / 1000:.2f}s"


def _phase2_detail(
    provider_completed: dict[str, int],
    provider_totals: dict[str, int],
    elapsed_ms: int,
) -> str:
    parts = [
        f"{_PROVIDER_LABELS[provider]} {provider_completed[provider]}/{provider_totals[provider]}"
        for provider in ("hmmer", "openprot", "clinvar", "synmicdb")
        if provider_totals[provider] > 0
    ]
    progress = ", ".join(parts) if parts else "No external lookups queued"
    return f"{progress} in {_format_elapsed_ms(elapsed_ms)}"


def _phase2_progress(
    provider_completed: dict[str, int],
    provider_totals: dict[str, int],
) -> tuple[int, int]:
    current = sum(provider_completed.values())
    total = sum(provider_totals.values())
    return current, total


def _candidate_variant_id(effect: FrameEffect) -> str:
    variant = effect.variant
    pos = variant.pos if variant else abs(effect.orf.pos)
    gene = variant.gene if variant else ""
    return f"{gene}_{effect.orf.frame}_{pos}"


def _protein_cache_key(protein: str) -> _ProteinKey:
    return sha256(protein.encode("utf-8")).hexdigest()


def _gene_cache_key(gene: str) -> _GeneKey:
    return gene.strip().upper()


def _variant_key(variant: NormalizedVariant) -> _VariantKey:
    return (
        variant.chrom.removeprefix("chr"),
        variant.pos,
        variant.ref,
        variant.alt,
        variant.gene.upper(),
    )


def _all_kmers(protein: str, k_min: int = 8, k_max: int = 11) -> list[Peptide]:
    """Generate all unique k-mers from a protein sequence.

    Used as a fallback when the mutation position (codon_pos) is unknown.
    Skips peptides containing stop codons (*) or unknown amino acids (X).
    """
    seen: set[str] = set()
    peptides: list[Peptide] = []
    for k in range(k_min, k_max + 1):
        for i in range(len(protein) - k + 1):
            seq = protein[i : i + k]
            if "*" in seq or "X" in seq:
                continue
            if seq not in seen:
                seen.add(seq)
                peptides.append(Peptide(sequence=seq, start=i, k=k))
    return peptides
