import type { FrameEffect } from '@/lib/types';
import { TIER_COLORS } from '@/lib/colors';
import EvidenceBadge from '@/components/ui/EvidenceBadge';

interface EvidencePanelProps {
  variant: FrameEffect;
}

export default function EvidencePanel({ variant }: EvidencePanelProps) {
  const { evidence_tier, synmicdb_score } = variant;
  const tierColor = TIER_COLORS[evidence_tier];

  return (
    <div data-testid="evidence-panel" className="glass rounded-xl p-4 flex flex-col gap-3">
      <h3 className="font-display text-sm font-semibold" style={{ color: '#22d3ee' }}>
        Evidence
      </h3>

      <div className="flex items-center gap-2">
        <EvidenceBadge tier={evidence_tier} />
      </div>

      {/* OpenProt */}
      <div className="flex items-center justify-between text-xs">
        <span style={{ color: '#64748b' }}>OpenProt AltORF</span>
        {evidence_tier >= 2 ? (
          <span className="font-data font-medium" style={{ color: '#60a5fa' }}>Confirmed ✓</span>
        ) : (
          <span style={{ color: '#475569' }}>Not found</span>
        )}
      </div>

      {/* SynMICdb */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between text-xs">
          <span style={{ color: '#64748b' }}>SynMICdb score</span>
          {synmicdb_score !== null ? (
            <span className="font-data font-medium" style={{ color: '#4ade80' }}>
              {synmicdb_score.toFixed(2)}
            </span>
          ) : (
            <span style={{ color: '#475569' }}>—</span>
          )}
        </div>
        {synmicdb_score !== null && (
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(74,222,128,0.1)' }}>
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${synmicdb_score * 100}%`, background: '#4ade80' }}
            />
          </div>
        )}
      </div>

      {/* ClinVar */}
      <div className="flex items-center justify-between text-xs">
        <span style={{ color: '#64748b' }}>ClinVar</span>
        <span style={{ color: '#475569' }}>Not in ClinVar</span>
      </div>

      {/* Tier legend */}
      <div
        className="mt-auto rounded-lg p-2 text-[10px]"
        style={{ background: `${tierColor}0a`, border: `1px solid ${tierColor}22` }}
      >
        <span style={{ color: tierColor }}>
          Tier {evidence_tier}:{' '}
          {evidence_tier === 1 && 'Computational scan only.'}
          {evidence_tier === 2 && 'ORF confirmed in OpenProt 2.0 proteogenomics data.'}
          {evidence_tier === 3 && 'High-recurrence variant in SynMICdb cancer cohort.'}
        </span>
      </div>
    </div>
  );
}
