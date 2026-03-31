import { TIER_COLORS, TIER_LABELS } from '@/lib/colors';

interface EvidenceBadgeProps {
  tier: 1 | 2 | 3;
  compact?: boolean;
  showLabel?: boolean;
}

export default function EvidenceBadge({
  tier,
  compact = false,
  showLabel = true,
}: EvidenceBadgeProps) {
  const color = TIER_COLORS[tier];
  const label = TIER_LABELS[tier];
  return (
    <span className="inline-flex items-center gap-1">
      {Array.from({ length: tier }).map((_, i) => (
        <span
          key={i}
          className={`inline-block rounded-full ${compact ? 'h-1.5 w-1.5' : 'h-2 w-2'}`}
          style={{ background: color, boxShadow: `0 0 4px ${color}88` }}
        />
      ))}
      {showLabel && (
        <span className={`${compact ? 'text-[10px]' : 'text-xs'} ml-1`} style={{ color }}>
          {label}
        </span>
      )}
    </span>
  );
}
