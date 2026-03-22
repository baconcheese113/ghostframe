'use client';

import { useState, Suspense, lazy } from 'react';
import type { FrameEffect, DemoSummary } from '@/lib/types';
import { DEMO_VARIANTS, DEMO_SUMMARY, DEMO_SANKEY, DEMO_SEQUENCE } from '@/lib/demo-data';

import NavBar from '@/components/dashboard/NavBar';
import PipelineTrace, { type ApiStep } from '@/components/dashboard/PipelineTrace';
import SummaryCards from '@/components/dashboard/SummaryCards';
import SankeyChart from '@/components/dashboard/SankeyChart';
import VariantTable from '@/components/dashboard/VariantTable';
import DetailRow from '@/components/dashboard/DetailRow';
import GenomeBrowser from '@/components/dashboard/GenomeBrowser';
import AnalysisPanel from '@/components/dashboard/AnalysisPanel';

// Heavy 3D components: lazy-loaded to keep initial bundle small
const DnaBackground = lazy(() => import('@/components/background/DnaBackground'));
const HelixExplorer = lazy(() => import('@/components/dashboard/HelixExplorer'));

const EMPTY_SUMMARY: DemoSummary = {
  total_silent: 0,
  reclassified: 0,
  frames_affected: 0,
  best_ic50: 0,
};

function locusFromVariant(v: FrameEffect): string {
  return `K02718.1:${Math.max(1, v.position - 50)}-${v.position + 50}`;
}

const DEMO_STEPS: ApiStep[] = [
  { name: 'MAF / FASTA',   status: 'success', detail: 'Demo · 1 sequence · 7,906 bp' },
  { name: 'Filter Silent', status: 'success', detail: '14 silent variants' },
  { name: 'Seq Fetch',     status: 'success', detail: 'K02718.1 · 7,906 bp' },
  { name: '6-Frame ORF',   status: 'success', detail: 'Demo ORF data' },
  { name: 'Reclassify',    status: 'success', detail: '14 reclassified' },
  { name: 'Peptides',      status: 'success', detail: '31 candidate peptides' },
  { name: 'MHC Binding',   status: 'success', detail: 'HLA-A*02:01 + HLA-B*07:02' },
  { name: 'Rank & Score',  status: 'success', detail: 'Best IC50: 142 nM' },
];

export default function DashboardPage() {
  const [selectedVariant, setSelectedVariant] = useState<FrameEffect | null>(null);
  const [panelOpen, setPanelOpen] = useState(true);
  const [hasResults, setHasResults] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [pipelineSteps, setPipelineSteps] = useState<ApiStep[] | undefined>(undefined);
  const [results, setResults] = useState<{
    variants: FrameEffect[];
    summary: DemoSummary;
  } | null>(null);

  const locus = selectedVariant ? locusFromVariant(selectedVariant) : 'K02718.1:1-300';

  function handleLoadDemo() {
    setPanelOpen(false);
    setApiError(null);
    setPipelineSteps(DEMO_STEPS);
    const demoResults = { variants: DEMO_VARIANTS, summary: DEMO_SUMMARY };
    setResults(demoResults);
    setHasResults(true);
    setSelectedVariant(DEMO_VARIANTS[0] ?? null);
  }

  async function handleAnalyze(opts: {
    accession: string;
    rawSequence: string | null;
    inputType: 'accession' | 'sequence';
  }) {
    setPanelOpen(false);
    setHasResults(false);
    setResults(null);
    setPipelineSteps(undefined);
    setIsLoading(true);
    setApiError(null);

    try {
      const res = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          accession: opts.accession,
          input_type: opts.inputType,
          raw_sequence: opts.rawSequence,
        }),
      });
      const data = await res.json();
      setPipelineSteps(data.steps ?? []);
      if (data.status === 'complete') {
        const r = { variants: data.variants ?? [], summary: data.summary ?? EMPTY_SUMMARY };
        setResults(r);
        setHasResults(true);
        setSelectedVariant((prev) => prev ?? r.variants[0] ?? null);
      } else {
        // API is up but pipeline errored — report honestly, leave results empty
        setApiError(data.error ?? 'Pipeline returned an error');
      }
    } catch {
      // Can't reach API — fall back to demo data so UI is usable offline
      setApiError('Backend not running — showing demo data');
      setPipelineSteps(DEMO_STEPS);
      const r = { variants: DEMO_VARIANTS, summary: DEMO_SUMMARY };
      setResults(r);
      setHasResults(true);
      setSelectedVariant((prev) => prev ?? r.variants[0] ?? null);
    }

    setIsLoading(false);
  }

  const displayVariants = results?.variants ?? [];
  const displaySummary = results?.summary ?? EMPTY_SUMMARY;

  return (
    <>
      {/* 3D background — fixed, behind everything, hidden on mobile */}
      <Suspense fallback={null}>
        <DnaBackground />
      </Suspense>

      {/* Foreground layout */}
      <div className="relative z-10 min-h-screen flex flex-col">
        <NavBar onTogglePanel={() => setPanelOpen((o) => !o)} />

        <main className="flex-1 px-3 sm:px-6 pb-10 space-y-4 pt-[4.5rem]">

          {/* Collapsible analysis input panel */}
          <AnalysisPanel
            open={panelOpen}
            onToggle={() => setPanelOpen((o) => !o)}
            onAnalyze={handleAnalyze}
            onLoadDemo={handleLoadDemo}
            isLoading={isLoading}
            apiError={apiError}
          />

          {/* Pipeline trace — data-driven from API step results */}
          <PipelineTrace steps={pipelineSteps} />

          {/* Summary stats */}
          <SummaryCards summary={displaySummary} />

          {/* Main visualization row — only after results land */}
          {hasResults && (
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Helix explorer — 62% width on desktop */}
              <div className="w-full lg:w-[62%]">
                <Suspense
                  fallback={
                    <div
                      className="glass rounded-xl flex items-center justify-center"
                      style={{ height: 360 }}
                    >
                      <span className="font-data text-xs" style={{ color: '#334155' }}>
                        Loading 3D viewer...
                      </span>
                    </div>
                  }
                >
                  <HelixExplorer variant={selectedVariant} sequence={DEMO_SEQUENCE} />
                </Suspense>
              </div>

              {/* Sankey — 38% width on desktop, below helix on mobile */}
              <div className="w-full lg:w-[38%]">
                <SankeyChart data={DEMO_SANKEY} />
              </div>
            </div>
          )}

          {/* Variant table */}
          <VariantTable
            variants={displayVariants}
            selectedId={selectedVariant?.id ?? null}
            onSelect={setSelectedVariant}
          />

          {/* Detail panels — animated, only when variant selected */}
          {hasResults && <DetailRow variant={selectedVariant} />}

          {/* Genome browser — hidden on mobile */}
          <div className="hidden sm:block">
            <GenomeBrowser locus={locus} />
          </div>

          <p className="text-center text-[10px] pb-2" style={{ color: '#334155' }}>
            GhostFrame · BIFS617 Capstone · Research &amp; educational use only
          </p>
        </main>
      </div>
    </>
  );
}
