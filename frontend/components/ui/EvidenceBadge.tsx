import { TIER_COLORS, TIER_LABELS } from '@/lib/colors';

interface EvidenceBadgeProps {
  tier: 1 | 2 | 3;
}

export default function EvidenceBadge({ tier }: EvidenceBadgeProps) {
  const color = TIER_COLORS[tier];
  const label = TIER_LABELS[tier];
  return (
    <span className="inline-flex items-center gap-1">
      {Array.from({ length: tier }).map((_, i) => (
        <span
          key={i}
          className="inline-block h-2 w-2 rounded-full"
          style={{ background: color, boxShadow: `0 0 4px ${color}88` }}
        />
      ))}
      <span className="text-xs ml-1" style={{ color }}>
        {label}
      </span>
    </span>
  );
}
