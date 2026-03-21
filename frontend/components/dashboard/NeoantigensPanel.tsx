import type { PeptidePrediction } from '@/lib/types';

interface NeoantigensPanelProps {
  peptides: PeptidePrediction[];
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

export default function NeoantigensPanel({ peptides }: NeoantigensPanelProps) {
  return (
    <div data-testid="neoantigen-panel" className="glass rounded-xl p-4 flex flex-col gap-3">
      <h3 className="font-display text-sm font-semibold" style={{ color: '#22d3ee' }}>
        Neoantigen Candidates
      </h3>

      {peptides.length === 0 ? (
        <p className="text-xs" style={{ color: '#475569' }}>No peptide predictions available.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(34,211,238,0.1)' }}>
                <th className="py-1.5 text-left font-medium pr-3" style={{ color: '#475569' }}>Peptide</th>
                <th className="py-1.5 text-left font-medium pr-3" style={{ color: '#475569' }}>Allele</th>
                <th className="py-1.5 text-right font-medium pr-3" style={{ color: '#475569' }}>IC50</th>
                <th className="py-1.5 text-right font-medium" style={{ color: '#475569' }}>Rank%</th>
              </tr>
            </thead>
            <tbody>
              {peptides.map((p, i) => {
                const color = ic50Color(p.ic50);
                return (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(34,211,238,0.06)' }}>
                    <td className="py-1.5 pr-3 font-data" style={{ color: '#e2f3ff', letterSpacing: '0.05em' }}>
                      {p.sequence}
                    </td>
                    <td className="py-1.5 pr-3 font-data text-[10px]" style={{ color: '#64748b' }}>
                      {p.allele}
                    </td>
                    <td className="py-1.5 pr-3 text-right">
                      <span className="font-data font-medium" style={{ color }}>
                        {p.ic50} nM
                      </span>
                      <span
                        className="ml-1 text-[9px] px-1 py-0.5 rounded"
                        style={{ background: `${color}18`, color, border: `1px solid ${color}44` }}
                      >
                        {ic50Label(p.ic50)}
                      </span>
                    </td>
                    <td className="py-1.5 text-right font-data" style={{ color: '#64748b' }}>
                      {p.rank.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-[10px] mt-auto" style={{ color: '#334155' }}>
        MHCflurry 2.2 · HLA-A*02:01 + HLA-B*07:02
      </p>
    </div>
  );
}
