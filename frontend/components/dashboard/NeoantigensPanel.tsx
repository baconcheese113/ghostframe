import type { DeepLaneEnrichment, FrameEffect } from '@/lib/types';

type DisplayCandidate = NonNullable<DeepLaneEnrichment['candidates']>[number] & {
  peptide_sequence: string;
  allele: string;
  ic50: number;
  rank: number;
};

interface NeoantigensPanelProps {
  variant: FrameEffect;
  enrichment: DeepLaneEnrichment | null;
  isEnriching?: boolean;
  hlaAlleles?: string[];
}

function ic50Color(ic50: number): string {
  if (ic50 < 50) return '#4ade80';
  if (ic50 < 500) return '#fbbf24';
  return '#475569';
}

function ic50Label(ic50: number): string {
  if (ic50 < 50) return 'Strong';
  if (ic50 < 500) return 'Moderate';
  return 'Weak';
}

function currentHlaLabel(hlaAlleles: string[]): string {
  return hlaAlleles.length > 0 ? hlaAlleles.join(', ') : 'HLA-A*02:01';
}

function hasDisplayBindingCandidate(
  candidate: DeepLaneEnrichment['candidates'][number],
): candidate is DisplayCandidate {
  return (
    typeof candidate.peptide_sequence === 'string' &&
    typeof candidate.allele === 'string' &&
    typeof candidate.ic50 === 'number' &&
    Number.isFinite(candidate.ic50) &&
    candidate.ic50 > 0 &&
    typeof candidate.rank === 'number' &&
    Number.isFinite(candidate.rank)
  );
}

export default function NeoantigensPanel({
  variant,
  enrichment,
  isEnriching = false,
  hlaAlleles = [],
}: NeoantigensPanelProps) {
  const deepCandidates = (enrichment?.candidates ?? []).filter(hasDisplayBindingCandidate);
  const hasDeepCandidates = deepCandidates.length > 0;
  const hasDeepNoBinderState = Boolean(enrichment) && !hasDeepCandidates;
  const hasFastPeptides = variant.peptides.length > 0;
  const hlaLabel = currentHlaLabel(hlaAlleles);

  return (
    <div data-testid="neoantigen-panel" className="glass rounded-xl p-4 flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <h3 className="font-display text-sm font-semibold" style={{ color: '#22d3ee' }}>
          Neoantigen Candidates
        </h3>
        <span className="text-[10px] font-data" style={{ color: '#64748b' }}>
          IC50 values shown for {hlaLabel} only.
        </span>
      </div>

      {isEnriching && !hasDeepCandidates && (
        <div className="flex items-center gap-2" style={{ color: '#22d3ee88' }}>
          <span
            className="inline-block h-2 w-2 rounded-full animate-pulse"
            style={{ background: '#22d3ee' }}
          />
          <span className="text-xs font-data">Enriching...</span>
        </div>
      )}

      {hasDeepCandidates && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(34,211,238,0.1)' }}>
                <th className="py-1.5 text-left font-medium pr-3" style={{ color: '#475569' }}>
                  Peptide
                </th>
                <th className="py-1.5 text-left font-medium pr-3" style={{ color: '#475569' }}>
                  Allele
                </th>
                <th className="py-1.5 text-right font-medium pr-3" style={{ color: '#475569' }}>
                  IC50
                </th>
                <th className="py-1.5 text-right font-medium" style={{ color: '#475569' }}>
                  Score
                </th>
              </tr>
            </thead>
            <tbody>
              {deepCandidates.slice(0, 8).map((candidate, index) => {
                const color = ic50Color(candidate.ic50);
                return (
                  <tr key={index} style={{ borderBottom: '1px solid rgba(34,211,238,0.06)' }}>
                    <td
                      className="py-1.5 pr-3 font-data"
                      style={{ color: '#e2f3ff', letterSpacing: '0.05em' }}
                    >
                      {candidate.peptide_sequence}
                    </td>
                    <td className="py-1.5 pr-3 font-data text-[10px]" style={{ color: '#64748b' }}>
                      {candidate.allele}
                    </td>
                    <td className="py-1.5 pr-3 text-right">
                      <span className="font-data font-medium" style={{ color }}>
                        {candidate.ic50.toFixed(0)} nM
                      </span>
                      <span
                        className="ml-1 text-[9px] px-1 py-0.5 rounded"
                        style={{
                          background: `${color}18`,
                          color,
                          border: `1px solid ${color}44`,
                        }}
                      >
                        {ic50Label(candidate.ic50)}
                      </span>
                    </td>
                    <td className="py-1.5 text-right font-data" style={{ color: '#64748b' }}>
                      {candidate.score.toFixed(3)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!isEnriching && hasDeepNoBinderState && (
        <div
          className="rounded-lg px-3 py-2 text-xs font-data"
          style={{
            background: 'rgba(100,116,139,0.08)',
            border: '1px solid rgba(100,116,139,0.18)',
            color: '#cbd5e1',
          }}
        >
          No supported MHC binder predicted for this variant under {hlaLabel}.
        </div>
      )}

      {!isEnriching && !hasDeepCandidates && !hasDeepNoBinderState && hasFastPeptides && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(34,211,238,0.1)' }}>
                <th className="py-1.5 text-left font-medium pr-3" style={{ color: '#475569' }}>
                  Peptide
                </th>
                <th className="py-1.5 text-left font-medium pr-3" style={{ color: '#475569' }}>
                  Allele
                </th>
                <th className="py-1.5 text-right font-medium pr-3" style={{ color: '#475569' }}>
                  IC50
                </th>
                <th className="py-1.5 text-right font-medium" style={{ color: '#475569' }}>
                  Rank%
                </th>
              </tr>
            </thead>
            <tbody>
              {variant.peptides.map((peptide, index) => {
                const color = ic50Color(peptide.ic50);
                return (
                  <tr key={index} style={{ borderBottom: '1px solid rgba(34,211,238,0.06)' }}>
                    <td
                      className="py-1.5 pr-3 font-data"
                      style={{ color: '#e2f3ff', letterSpacing: '0.05em' }}
                    >
                      {peptide.sequence}
                    </td>
                    <td className="py-1.5 pr-3 font-data text-[10px]" style={{ color: '#64748b' }}>
                      {peptide.allele}
                    </td>
                    <td className="py-1.5 pr-3 text-right">
                      <span className="font-data font-medium" style={{ color }}>
                        {peptide.ic50.toFixed(0)} nM
                      </span>
                    </td>
                    <td className="py-1.5 text-right font-data" style={{ color: '#64748b' }}>
                      {peptide.rank.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!isEnriching && !hasDeepCandidates && !hasDeepNoBinderState && !hasFastPeptides && (
        <p className="text-xs" style={{ color: '#475569' }}>
          No peptide predictions available.
        </p>
      )}

      <p className="text-[10px] mt-auto" style={{ color: '#334155' }}>
        MHCflurry 2.2 / run allele {hlaLabel}
      </p>
    </div>
  );
}
