import type { DeepLaneEnrichment, FrameEffect } from '@/lib/types';
import { TIER_COLORS } from '@/lib/colors';
import EvidenceBadge from '@/components/ui/EvidenceBadge';
import SynmicdbScore from '@/components/ui/SynmicdbScore';

interface EvidencePanelProps {
  variant: FrameEffect;
  enrichment: DeepLaneEnrichment | null;
  isEnriching?: boolean;
}

export default function EvidencePanel({
  variant,
  enrichment,
  isEnriching = false,
}: EvidencePanelProps) {
  const { evidence_tier, synmicdb_score } = variant;
  const tierColor = TIER_COLORS[evidence_tier];

  const ev = enrichment?.evidence;
  const displayTier = ev?.tier === 3 ? 3 : ev?.tier === 2 ? 2 : evidence_tier;
  const displaySynmicdb = ev?.synmicdb_score ?? synmicdb_score;
  const openprotAccession = ev?.openprot_accession ?? null;
  const openprotType = ev?.openprot_type ?? null;
  const clinvarSig = ev?.clinvar_significance ?? variant.clinvar_significance ?? null;
  const displayTierColor = TIER_COLORS[displayTier] ?? tierColor;

  return (
    <div data-testid="evidence-panel" className="glass rounded-xl p-4 flex flex-col gap-3">
      <h3 className="font-display text-sm font-semibold" style={{ color: '#22d3ee' }}>
        Evidence
      </h3>

      {isEnriching && !enrichment && (
        <div className="flex items-center gap-2" style={{ color: '#22d3ee88' }}>
          <span
            className="inline-block h-2 w-2 rounded-full animate-pulse"
            style={{ background: '#22d3ee' }}
          />
          <span className="text-xs font-data">Enriching...</span>
        </div>
      )}

      <div className="flex items-center gap-2">
        <EvidenceBadge tier={displayTier} />
      </div>

      <div className="flex items-center justify-between text-xs gap-3">
        <span style={{ color: '#64748b' }}>OpenProt AltORF</span>
        {openprotAccession ? (
          <span className="font-data font-medium text-[10px] text-right" style={{ color: '#60a5fa' }}>
            {openprotAccession} / {openprotType ?? 'AltORF'} / confirmed
          </span>
        ) : displayTier >= 2 ? (
          <span className="font-data font-medium" style={{ color: '#60a5fa' }}>
            Confirmed
          </span>
        ) : (
          <span style={{ color: '#475569' }}>Not found</span>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs gap-3">
          <span style={{ color: '#64748b' }}>SynMICdb score</span>
          <div className="w-28">
            <SynmicdbScore score={displaySynmicdb} />
          </div>
        </div>
        <span className="text-[10px] font-data" style={{ color: '#475569' }}>
          Positive scores suggest stronger SynMICdb support, values near 0 are weak or neutral,
          and negative scores suggest little support.
        </span>
      </div>

      <div className="flex items-center justify-between text-xs gap-3">
        <span style={{ color: '#64748b' }}>ClinVar</span>
        {clinvarSig ? (
          <span className="font-data font-medium text-right" style={{ color: '#fbbf24' }}>
            {clinvarSig}
          </span>
        ) : (
          <span style={{ color: '#475569' }}>Not in ClinVar</span>
        )}
      </div>

      <div
        className="mt-auto rounded-lg p-2 text-[10px]"
        style={{
          background: `${displayTierColor}0a`,
          border: `1px solid ${displayTierColor}22`,
        }}
      >
        <span style={{ color: displayTierColor }}>
          Tier {displayTier}:{' '}
          {displayTier === 1 && 'Computational scan only.'}
          {displayTier === 2 && 'ORF confirmed in OpenProt 2.0 proteogenomics data.'}
          {displayTier === 3 && 'High-recurrence variant in SynMICdb cancer cohort.'}
        </span>
      </div>
    </div>
  );
}
