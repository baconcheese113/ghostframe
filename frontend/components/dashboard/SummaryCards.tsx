'use client';

import { useEffect, useRef } from 'react';
import { animate } from 'motion/react';
import type { DemoSummary } from '@/lib/types';

interface SummaryCardsProps {
  summary: DemoSummary;
}

const CARDS = [
  {
    key: 'total_silent_variants' as const,
    label: 'Silent Variants',
    suffix: '',
    color: '#22d3ee',
    description: 'silent inputs retained',
  },
  {
    key: 'reclassified_effects' as const,
    label: 'Reclassified Effects',
    suffix: '',
    color: '#fb923c',
    description: 'non-silent ORF effects',
  },
  {
    key: 'total_effects' as const,
    label: 'ORF Effects',
    suffix: '',
    color: '#818cf8',
    description: 'rows in the effect table',
  },
  {
    key: 'best_ic50' as const,
    label: 'Best IC50',
    suffix: ' nM',
    color: '#4ade80',
    description: 'strongest binder for current HLA',
  },
];

export default function SummaryCards({ summary }: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {CARDS.map((card) => (
        <CountCard
          key={card.key}
          label={card.label}
          target={summary[card.key] ?? null}
          suffix={card.suffix}
          color={card.color}
          description={card.description}
        />
      ))}
    </div>
  );
}

function CountCard({
  label,
  target,
  suffix,
  color,
  description,
}: {
  label: string;
  target: number | null;
  suffix: string;
  color: string;
  description: string;
}) {
  const numRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!numRef.current || target === null) return;
    const el = numRef.current;
    const startValue = Number(el.textContent?.replace(/[^0-9.-]/g, '') ?? '0') || 0;
    const controls = animate(startValue, target, {
      duration: 1.4,
      ease: 'easeOut',
      onUpdate(value) {
        el.textContent = Math.round(value).toString();
      },
    });
    return () => controls.stop();
  }, [target]);

  return (
    <div className="glass rounded-xl p-4 flex flex-col gap-2" style={{ borderColor: `${color}22` }}>
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium" style={{ color: '#64748b' }}>
          {label}
        </span>
        <span
          className="h-2 w-2 rounded-full mt-1"
          style={{ background: color, boxShadow: `0 0 6px ${color}` }}
        />
      </div>
      <div className="font-display text-3xl font-bold tracking-tight" style={{ color }}>
        <span ref={numRef}>{target === null ? '--' : '0'}</span>
        {target !== null && (
          <span className="text-lg font-normal" style={{ color: `${color}99` }}>
            {suffix}
          </span>
        )}
      </div>
      <span className="text-[11px]" style={{ color: '#475569' }}>
        {description}
      </span>
    </div>
  );
}
