'use client';

interface SynmicdbScoreProps {
  score: number | null;
  compact?: boolean;
}

const DISPLAY_RANGE = 4;

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export default function SynmicdbScore({ score, compact = false }: SynmicdbScoreProps) {
  if (score === null || !Number.isFinite(score)) {
    return (
      <div className="flex items-center justify-end text-xs font-data" style={{ color: '#475569' }}>
        --
      </div>
    );
  }

  const clamped = clamp(score, -DISPLAY_RANGE, DISPLAY_RANGE);
  const magnitude = Math.abs(clamped) / DISPLAY_RANGE;
  const isNeutral = Math.abs(clamped) < 0.05;
  const isPositive = clamped > 0;
  const barWidthPercent = magnitude * 50;
  const valueColor = isNeutral ? '#94a3b8' : isPositive ? '#4ade80' : '#f87171';
  const trackHeight = compact ? 5 : 7;
  const barGradient = isNeutral
    ? 'linear-gradient(90deg, rgba(148,163,184,0.4), rgba(148,163,184,0.75))'
    : isPositive
      ? 'linear-gradient(90deg, rgba(74,222,128,0.35), rgba(74,222,128,0.95))'
      : 'linear-gradient(90deg, rgba(248,113,113,0.95), rgba(248,113,113,0.35))';

  const track = (
    <div
      className="relative overflow-hidden rounded-full"
      style={{
        height: trackHeight,
        background: 'rgba(15,23,42,0.9)',
        border: '1px solid rgba(100,116,139,0.18)',
      }}
    >
      <div
        className="absolute inset-y-0 left-1/2 w-px"
        style={{ background: 'rgba(148,163,184,0.35)' }}
      />
      {barWidthPercent > 0 && (
        <div
          className="absolute top-0 bottom-0"
          style={{
            left: isPositive ? '50%' : `${50 - barWidthPercent}%`,
            width: `${barWidthPercent}%`,
            background: barGradient,
          }}
        />
      )}
    </div>
  );

  if (compact) {
    return (
      <div className="flex min-w-0 items-center justify-end gap-1.5">
        <div className="w-[3.75rem]">{track}</div>
        <span
          className="w-[2.75rem] text-right text-[10px] font-data font-medium tabular-nums"
          style={{ color: valueColor }}
        >
          {score.toFixed(2)}
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 min-w-[6.5rem]">
      <span
        className="text-right text-[10px] font-data font-medium tabular-nums"
        style={{ color: valueColor }}
      >
        {score.toFixed(2)}
      </span>
      {track}
    </div>
  );
}
