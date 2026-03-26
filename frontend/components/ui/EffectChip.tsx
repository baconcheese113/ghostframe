import { EFFECT_COLORS } from '@/lib/colors';
import type { EffectType } from '@/lib/types';

interface EffectChipProps {
  effect: EffectType;
  small?: boolean;
}

export default function EffectChip({ effect, small }: EffectChipProps) {
  const color = EFFECT_COLORS[effect] ?? '#475569';
  return (
    <span
      className={`inline-flex items-center rounded font-data font-medium ${small ? 'px-1.5 py-0.5 text-xs' : 'px-2 py-0.5 text-xs'}`}
      style={{
        background: `${color}18`,
        border: `1px solid ${color}40`,
        color: color,
      }}
    >
      {effect}
    </span>
  );
}
