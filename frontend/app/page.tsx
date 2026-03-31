'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import config from '@/lib/config';
import type {
  AnalysisMeta,
  ApiWarning,
  DeepLaneCandidate,
  DeepLaneEnrichment,
  DemoSummary,
  FrameEffect,
  VariantProcessingStatus,
} from '@/lib/types';

import NavBar from '@/components/dashboard/NavBar';
import PipelineTrace, { type ApiStep } from '@/components/dashboard/PipelineTrace';
import SummaryCards from '@/components/dashboard/SummaryCards';
import VariantTable from '@/components/dashboard/VariantTable';
import DetailRow from '@/components/dashboard/DetailRow';
import AnalysisPanel from '@/components/dashboard/AnalysisPanel';
import ReadingFrameViewer from '@/components/dashboard/ReadingFrameViewer';
import LandingExplainer from '@/components/dashboard/LandingExplainer';

const DnaBackground = dynamic(() => import('@/components/background/DnaBackground'), { ssr: false });

const EMPTY_SUMMARY: DemoSummary = {
  total_input_variants: 0,
  total_silent_variants: 0,
  total_orfs: 0,
  total_effects: 0,
  reclassified_effects: 0,
  total_silent: 0,
  reclassified: 0,
  frames_affected: 0,
  best_ic50: null,
};

const EMPTY_ANALYSIS_META: AnalysisMeta = {
  primary_label: 'Awaiting analysis',
  secondary_label: 'Upload MAF or use demo data',
  sample_count: 0,
  variant_count: 0,
  is_demo: false,
  hla_alleles: [],
};

const DEFAULT_HLA_ALLELES = ['HLA-A*02:01'];

function upsertStep(steps: ApiStep[] | undefined, nextStep: ApiStep): ApiStep[] {
  const existing = steps ?? [];
  const index = existing.findIndex((step) => step.name === nextStep.name);
  if (index === -1) {
    return [...existing, nextStep];
  }

  return existing.map((step, stepIndex) => (stepIndex === index ? nextStep : step));
}

function normalizeTier(tier: number | null | undefined): 1 | 2 | 3 {
  if (tier === 3) return 3;
  if (tier === 2) return 2;
  return 1;
}

function isScoredCandidate(candidate: DeepLaneCandidate): boolean {
  return (
    typeof candidate.peptide_sequence === 'string' &&
    candidate.peptide_sequence.length > 0 &&
    typeof candidate.allele === 'string' &&
    candidate.allele.length > 0 &&
    typeof candidate.ic50 === 'number' &&
    Number.isFinite(candidate.ic50) &&
    candidate.ic50 > 0 &&
    typeof candidate.rank === 'number' &&
    Number.isFinite(candidate.rank)
  );
}

function mergeEnrichmentIntoVariants(
  variants: FrameEffect[],
  variantId: string,
  enrichment: DeepLaneEnrichment,
): FrameEffect[] {
  const scoredCandidates = enrichment.candidates.filter(isScoredCandidate);

  return variants.map((variant) => {
    if (variant.id !== variantId) {
      return variant;
    }

    return {
      ...variant,
      evidence_tier: normalizeTier(enrichment.evidence?.tier),
      synmicdb_score: enrichment.evidence?.synmicdb_score ?? null,
      clinvar_significance: enrichment.evidence?.clinvar_significance ?? null,
      peptides: scoredCandidates.map((candidate) => ({
        sequence: candidate.peptide_sequence,
        allele: candidate.allele,
        ic50: candidate.ic50,
        rank: candidate.rank,
      })),
    };
  });
}

function mergeEnrichmentIntoSummary(
  summary: DemoSummary,
  enrichment: DeepLaneEnrichment,
): DemoSummary {
  const candidateIc50s = enrichment.candidates
    .map((candidate) => candidate.ic50)
    .filter((ic50): ic50 is number => typeof ic50 === 'number' && Number.isFinite(ic50) && ic50 > 0);

  if (candidateIc50s.length === 0) {
    return summary;
  }

  const nextBest = Math.min(...candidateIc50s);
  return {
    ...summary,
    best_ic50:
      summary.best_ic50 === null ? nextBest : Math.min(summary.best_ic50, nextBest),
  };
}

function upsertWarning(
  warnings: ApiWarning[],
  nextWarning: ApiWarning,
): ApiWarning[] {
  const warningKey = `${nextWarning.provider ?? 'provider'}:${nextWarning.message ?? 'message'}:${nextWarning.variant_id ?? ''}`;
  if (
    warnings.some(
      (warning) =>
        `${warning.provider ?? 'provider'}:${warning.message ?? 'message'}:${warning.variant_id ?? ''}` === warningKey,
    )
  ) {
    return warnings;
  }
  return [...warnings, nextWarning];
}

function buildPendingAnalysisMeta(opts: {
  mafContent: string | null;
  mafFilename: string | null;
}): AnalysisMeta {
  if (opts.mafContent === null) {
    return {
      primary_label: 'Demo dataset',
      secondary_label: 'Running analysis',
      sample_count: 0,
      variant_count: 0,
      is_demo: true,
      hla_alleles: DEFAULT_HLA_ALLELES,
    };
  }

  return {
    primary_label: opts.mafFilename?.trim() || 'Uploaded MAF',
    secondary_label: 'Running analysis',
    sample_count: 0,
    variant_count: 0,
    is_demo: false,
    hla_alleles: DEFAULT_HLA_ALLELES,
  };
}

function coerceAnalysisMeta(value: unknown, fallback: AnalysisMeta): AnalysisMeta {
  if (!value || typeof value !== 'object') {
    return fallback;
  }

  const meta = value as Partial<AnalysisMeta>;
  const nextHlaAlleles = Array.isArray(meta.hla_alleles)
    ? meta.hla_alleles.filter((allele): allele is string => typeof allele === 'string' && allele.length > 0)
    : fallback.hla_alleles;
  return {
    primary_label:
      typeof meta.primary_label === 'string' && meta.primary_label.length > 0
        ? meta.primary_label
        : fallback.primary_label,
    secondary_label:
      typeof meta.secondary_label === 'string'
        ? meta.secondary_label
        : meta.secondary_label === null
          ? null
          : fallback.secondary_label,
    sample_count:
      typeof meta.sample_count === 'number' && Number.isFinite(meta.sample_count)
        ? meta.sample_count
        : fallback.sample_count,
    variant_count:
      typeof meta.variant_count === 'number' && Number.isFinite(meta.variant_count)
        ? meta.variant_count
        : fallback.variant_count,
    is_demo: typeof meta.is_demo === 'boolean' ? meta.is_demo : fallback.is_demo,
    hla_alleles: nextHlaAlleles.length > 0 ? nextHlaAlleles : fallback.hla_alleles,
  };
}

function buildInitialVariantStatuses(variants: FrameEffect[]): Record<string, VariantProcessingStatus> {
  return Object.fromEntries(
    variants.map((variant) => [
      variant.id,
      variant.new_class === 'Silent' ? 'scan_only' : 'enriching',
    ]),
  );
}

function variantStatusForEnrichment(enrichment: DeepLaneEnrichment): VariantProcessingStatus {
  return enrichment.candidates.some(isScoredCandidate) ? 'scored' : 'no_binding';
}

function formatHlaAlleles(alleles: string[]): string {
  return alleles.length > 0 ? alleles.join(', ') : DEFAULT_HLA_ALLELES.join(', ');
}

function buildCountChain(summary: DemoSummary): string {
  return [
    `${summary.total_input_variants} input variants`,
    `${summary.total_silent_variants} silent variants`,
    `${summary.total_orfs} ORFs scanned`,
    `${summary.total_effects} ORF effects`,
    `${summary.reclassified_effects} reclassified effects`,
  ].join(' -> ');
}

function AnalysisAlerts({
  warnings,
  error,
}: {
  warnings: ApiWarning[];
  error: string | null;
}) {
  if (!warnings.length && !error) {
    return null;
  }

  return (
    <div data-testid="analysis-alerts" className="flex flex-col gap-2">
      {warnings.length > 0 && (
        <div
          className="glass rounded-xl px-4 py-3 text-[11px] font-data"
          style={{
            background: 'rgba(251,191,36,0.05)',
            border: '1px solid rgba(251,191,36,0.16)',
            color: '#cbd5e1',
          }}
        >
          <div className="mb-1" style={{ color: '#fbbf24' }}>
            Warnings ({warnings.length})
          </div>
          <div className="flex flex-col gap-1">
            {warnings.slice(0, 3).map((warning, index) => (
              <span key={`${warning.provider ?? 'provider'}-${warning.message ?? 'message'}-${index}`}>
                {(warning.provider ?? 'Provider').toUpperCase()}: {warning.message ?? 'Partial evidence unavailable.'}
              </span>
            ))}
            {warnings.length > 3 && (
              <span style={{ color: '#94a3b8' }}>
                +{warnings.length - 3} more warning(s)
              </span>
            )}
          </div>
        </div>
      )}

      {error && (
        <div
          className="glass rounded-xl px-4 py-3 text-[11px] font-data"
          style={{
            background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.16)',
            color: '#cbd5e1',
          }}
        >
          Error: {error}
        </div>
      )}
    </div>
  );
}


export default function DashboardPage() {
  const abortControllerRef = useRef<AbortController | null>(null);
  const detailRowRef = useRef<HTMLDivElement | null>(null);
  const shouldRevealDetailsRef = useRef(false);

  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(true);
  const [hasSubmittedAnalysis, setHasSubmittedAnalysis] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [apiWarnings, setApiWarnings] = useState<ApiWarning[]>([]);
  const [runningStep, setRunningStep] = useState<string | null>(null);
  const [runningDetail, setRunningDetail] = useState<string | null>(null);
  const [runningElapsedMs, setRunningElapsedMs] = useState<number | null>(null);
  const [runningProgressCurrent, setRunningProgressCurrent] = useState<number | null>(null);
  const [runningProgressTotal, setRunningProgressTotal] = useState<number | null>(null);
  const [pipelineSteps, setPipelineSteps] = useState<ApiStep[] | undefined>(undefined);
  const [results, setResults] = useState<{ variants: FrameEffect[]; summary: DemoSummary } | null>(null);
  const [analysisMeta, setAnalysisMeta] = useState<AnalysisMeta>(EMPTY_ANALYSIS_META);
  const [variantWindows, setVariantWindows] = useState<Record<string, string>>({});
  const [enrichments, setEnrichments] = useState<Record<string, DeepLaneEnrichment>>({});
  const [variantStatuses, setVariantStatuses] = useState<Record<string, VariantProcessingStatus>>({});

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // useEffect(() => {
  //   if (!shouldRevealDetailsRef.current || !detailRowRef.current || !selectedVariantId) {
  //     return;
  //   }

  //   const frameId = window.requestAnimationFrame(() => {
  //     detailRowRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  //     shouldRevealDetailsRef.current = false;
  //   });

  //   return () => {
  //     window.cancelAnimationFrame(frameId);
  //   };
  // }, [selectedVariantId]);

  async function handleAnalyze(opts: { mafContent: string | null; mafFilename: string | null }) {
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setHasSubmittedAnalysis(true);
    setPanelOpen(false);
    setHasResults(false);
    setResults(null);
    setSelectedVariantId(null);
    setPipelineSteps(undefined);
    setRunningStep(null);
    setRunningDetail(null);
    setRunningElapsedMs(null);
    setRunningProgressCurrent(null);
    setRunningProgressTotal(null);
    setEnrichments({});
    setVariantWindows({});
    setVariantStatuses({});
    setApiWarnings([]);
    setIsLoading(true);
    setApiError(null);
    setAnalysisMeta(buildPendingAnalysisMeta(opts));

    try {
      const handleStreamEvent = (ev: Record<string, unknown>) => {
        if (ev.type === 'running') {
          setRunningStep(typeof ev.name === 'string' ? ev.name : null);
          setRunningDetail(typeof ev.detail === 'string' ? ev.detail : null);
          setRunningElapsedMs(typeof ev.elapsed_ms === 'number' ? ev.elapsed_ms : null);
          setRunningProgressCurrent(
            typeof ev.progress_current === 'number' ? ev.progress_current : null,
          );
          setRunningProgressTotal(
            typeof ev.progress_total === 'number' ? ev.progress_total : null,
          );
        } else if (ev.type === 'step') {
          setRunningStep(null);
          setRunningDetail(null);
          setRunningElapsedMs(null);
          setRunningProgressCurrent(null);
          setRunningProgressTotal(null);
          setPipelineSteps((prev) =>
            upsertStep(prev, {
              name: ev.name as string,
              status: ev.status as string,
              detail: ev.detail as string,
              elapsed_ms: typeof ev.elapsed_ms === 'number' ? ev.elapsed_ms : undefined,
            }),
          );
        } else if (ev.type === 'fast_complete') {
          const variants = (ev.variants as FrameEffect[]) ?? [];
          const summary = (ev.summary as DemoSummary) ?? EMPTY_SUMMARY;
          setResults({ variants, summary });
          setVariantStatuses(buildInitialVariantStatuses(variants));
          setVariantWindows((ev.variant_windows as Record<string, string>) ?? {});
          setAnalysisMeta((prev) => coerceAnalysisMeta(ev.analysis_meta, prev));
          setHasResults(true);
          const initialVariant =
            variants.find((variant) => variant.new_class !== 'Silent') ?? variants[0] ?? null;
          setSelectedVariantId((prev) => prev ?? initialVariant?.id ?? null);
        } else if (ev.type === 'enrich_complete') {
          const variantId = ev.variant_id as string;
          const enrichment: DeepLaneEnrichment = {
            candidates: (ev.candidates as DeepLaneEnrichment['candidates']) ?? [],
            evidence: ev.evidence as DeepLaneEnrichment['evidence'],
          };

          setEnrichments((prev) => ({
            ...prev,
            [variantId]: enrichment,
          }));
          setVariantStatuses((prev) => ({
            ...prev,
            [variantId]: variantStatusForEnrichment(enrichment),
          }));
          setResults((prev) =>
            prev
              ? {
                  variants: mergeEnrichmentIntoVariants(prev.variants, variantId, enrichment),
                  summary: mergeEnrichmentIntoSummary(prev.summary, enrichment),
                }
              : prev,
          );
        } else if (ev.type === 'warning') {
          setApiWarnings((prev) =>
            upsertWarning(prev, {
              provider: typeof ev.provider === 'string' ? ev.provider : null,
              message: typeof ev.message === 'string' ? ev.message : null,
              variant_id: typeof ev.variant_id === 'string' ? ev.variant_id : null,
              fatal: Boolean(ev.fatal),
              elapsed_ms: typeof ev.elapsed_ms === 'number' ? ev.elapsed_ms : undefined,
            }),
          );
        } else if (ev.type === 'complete') {
          setRunningStep(null);
          setRunningDetail(null);
          setRunningElapsedMs(null);
          setRunningProgressCurrent(null);
          setRunningProgressTotal(null);
          setIsLoading(false);
        } else if (ev.type === 'error') {
          setApiError(ev.error as string);
          setRunningStep(null);
          setRunningDetail(null);
          setRunningElapsedMs(null);
          setRunningProgressCurrent(null);
          setRunningProgressTotal(null);
          setIsLoading(false);
        }
      };

      const res = await fetch(`${config.apiUrl}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          maf_content: opts.mafContent,
          maf_filename: opts.mafFilename,
        }),
        signal: controller.signal,
      });

      if (!res.body) throw new Error('No response body');
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (value) {
          buffer += decoder.decode(value, { stream: !done });
        }
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.trim()) continue;
          let ev: Record<string, unknown>;
          try {
            ev = JSON.parse(line);
          } catch {
            continue;
          }
          handleStreamEvent(ev);
        }

        if (done && buffer.trim()) {
          try {
            handleStreamEvent(JSON.parse(buffer));
          } catch {
            // Ignore incomplete trailing payloads.
          }
          buffer = '';
        }

        if (done) {
          break;
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }
      setApiError(err instanceof Error ? err.message : 'Could not reach API');
      setIsLoading(false);
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    }
  }

  function handleSelectVariant(variant: FrameEffect) {
    shouldRevealDetailsRef.current = true;
    setSelectedVariantId(variant.id);
  }

  const showAnalysisPanel = panelOpen || !hasSubmittedAnalysis;
  const displayVariants = results?.variants ?? [];
  const displaySummary = results?.summary ?? EMPTY_SUMMARY;
  const selectedVariant =
    displayVariants.find((variant) => variant.id === selectedVariantId) ??
    displayVariants[0] ??
    null;
  const selectedVariantStatus = selectedVariant
    ? variantStatuses[selectedVariant.id] ??
      (selectedVariant.new_class === 'Silent' ? 'scan_only' : 'enriching')
    : null;

  const windowKey = selectedVariant
    ? `${selectedVariant.gene}_${selectedVariant.position}`
    : '';
  const windowSequence = variantWindows[windowKey] ?? '';
  const selectedEffects = selectedVariant
    ? displayVariants.filter(
        (effect) => effect.gene === selectedVariant.gene && effect.position === selectedVariant.position,
      )
    : [];
  const currentHlaLabel = formatHlaAlleles(analysisMeta.hla_alleles);

  return (
    <>
      <Suspense fallback={null}>
        <DnaBackground />
      </Suspense>

      <div className="relative z-10 min-h-screen flex flex-col">
        <NavBar
          analysisMeta={analysisMeta}
          onTogglePanel={() => setPanelOpen((open) => !open)}
        />

        <main className={`flex-1 px-3 sm:px-6 pb-10 space-y-4 ${showAnalysisPanel ? 'pt-4' : 'pt-2'}`}>
          {showAnalysisPanel && (
            <AnalysisPanel
              open={panelOpen}
              onToggle={() => setPanelOpen((open) => !open)}
              onAnalyze={handleAnalyze}
              isLoading={isLoading}
              apiError={apiError}
              warnings={apiWarnings}
            />
          )}

          {!showAnalysisPanel && <AnalysisAlerts warnings={apiWarnings} error={apiError} />}

          <PipelineTrace
            steps={pipelineSteps}
            runningStep={runningStep}
            runningDetail={runningDetail}
            runningElapsedMs={runningElapsedMs}
            runningProgressCurrent={runningProgressCurrent}
            runningProgressTotal={runningProgressTotal}
          />

          {hasResults ? <SummaryCards summary={displaySummary} /> : !isLoading && <LandingExplainer />}

          {hasResults && (
            <div
              data-testid="count-explainer"
              className="glass rounded-xl px-4 py-3 flex flex-col gap-1"
            >
              <span className="text-[11px] font-data" style={{ color: '#cbd5e1' }}>
                {buildCountChain(displaySummary)}
              </span>
              <span className="text-[10px] font-data" style={{ color: '#64748b' }}>
                Each table row is an ORF effect. One silent variant can overlap multiple ORFs and
                produce multiple effect rows.
              </span>
            </div>
          )}

          {hasResults && (
            <div
              className="glass rounded-xl overflow-hidden px-3 py-2"
              style={{ maxHeight: '44vh', overflowY: 'auto' }}
            >
              <ReadingFrameViewer
                effects={selectedEffects}
                windowSequence={windowSequence}
                variantRef={selectedVariant?.ref ?? ''}
                variantAlt={selectedVariant?.alt ?? ''}
                variantInWindow={selectedVariant?.variant_in_window ?? 500}
                selectedEffect={selectedVariant}
              />
            </div>
          )}

          {hasResults && (
            <VariantTable
              variants={displayVariants}
              variantStatuses={variantStatuses}
              selectedId={selectedVariant?.id ?? null}
              onSelect={handleSelectVariant}
              summary={displaySummary}
              hlaLabel={currentHlaLabel}
            />
          )}

          {hasResults && (
            <div ref={detailRowRef}>
              <DetailRow
                variant={selectedVariant}
                enrichment={selectedVariant ? (enrichments[selectedVariant.id] ?? null) : null}
                isLoading={selectedVariantStatus === 'enriching'}
                hlaAlleles={analysisMeta.hla_alleles}
              />
            </div>
          )}

          <p className="text-center text-[10px] pb-2" style={{ color: '#334155' }}>
            GhostFrame - BIFS617 Capstone - Research &amp; educational use only
          </p>
        </main>
      </div>
    </>
  );
}
