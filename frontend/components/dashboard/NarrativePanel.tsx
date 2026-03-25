import type { FrameEffect } from '@/lib/types';

interface NarrativePanelProps {
  variant: FrameEffect;
}

export default function NarrativePanel({ variant }: NarrativePanelProps) {
  return (
    <div data-testid="narrative-panel" className="glass rounded-xl p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold" style={{ color: '#22d3ee' }}>
          AI Interpretation
        </h3>
        <span
          className="text-[9px] px-2 py-0.5 rounded-full font-data"
          style={{ background: 'rgba(129,140,248,0.12)', color: '#818cf8', border: '1px solid rgba(129,140,248,0.3)' }}
        >
          GPT-assisted
        </span>
      </div>

      <div className="font-display text-xs leading-relaxed" style={{ color: '#94a3b8' }}>
        <span className="font-data font-medium mr-1" style={{ color: '#22d3ee' }}>
          {variant.gene} p.{variant.position}
        </span>
        — {variant.narrative}
      </div>

      <div
        className="rounded-lg p-2 text-[10px] leading-relaxed mt-auto"
        style={{ background: 'rgba(251,146,60,0.06)', border: '1px solid rgba(251,146,60,0.18)' }}
      >
        <span style={{ color: '#fb923c' }}>
          Research & educational use only. Not for clinical decision-making. Consult a qualified clinician before drawing conclusions from these predictions.
        </span>
      </div>
    </div>
  );
}
