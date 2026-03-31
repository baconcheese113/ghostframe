'use client';

import type { AnalysisMeta } from '@/lib/types';

interface NavBarProps {
  onTogglePanel: () => void;
  analysisMeta?: AnalysisMeta | null;
}

const DEFAULT_ANALYSIS_META: AnalysisMeta = {
  primary_label: 'Awaiting analysis',
  secondary_label: 'Upload MAF or use demo data',
  sample_count: 0,
  variant_count: 0,
  is_demo: false,
  hla_alleles: [],
};

export default function NavBar({ onTogglePanel, analysisMeta = null }: NavBarProps) {
  const currentMeta = analysisMeta ?? DEFAULT_ANALYSIS_META;

  return (
    <nav
      className="glass-strong sticky top-0 z-50 flex items-center justify-between px-4 sm:px-6 py-3"
      style={{ minHeight: '52px' }}
    >
      {/* Logo */}
      <span
        className="font-display text-lg sm:text-xl font-bold tracking-widest"
        style={{ color: '#22d3ee', letterSpacing: '0.2em' }}
      >
        GHOSTFRAME
      </span>

      {/* Dataset chip */}
      <div
        data-testid="analysis-label"
        title={
          currentMeta.secondary_label
            ? `${currentMeta.primary_label} / ${currentMeta.secondary_label}`
            : currentMeta.primary_label
        }
        className="hidden sm:flex items-center gap-2 rounded-full px-3 py-1 text-xs font-data max-w-[52rem]"
        style={{
          background: 'rgba(34,211,238,0.08)',
          border: '1px solid rgba(34,211,238,0.2)',
          color: '#94a3b8',
        }}
      >
        <span
          className="h-1.5 w-1.5 rounded-full"
          style={{ background: '#4ade80', boxShadow: '0 0 6px #4ade80' }}
        />
        <span className="truncate" style={{ color: '#d7f6ff' }}>
          {currentMeta.primary_label}
        </span>
        {currentMeta.secondary_label && (
          <span className="truncate" style={{ color: '#64748b' }}>
            / {currentMeta.secondary_label}
          </span>
        )}
      </div>

      {/* New Analysis button */}
      <button
        onClick={onTogglePanel}
        className="flex items-center gap-2 rounded-lg px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium transition-all"
        style={{
          background: 'rgba(34,211,238,0.1)',
          border: '1px solid rgba(34,211,238,0.25)',
          color: '#22d3ee',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLButtonElement).style.background = 'rgba(34,211,238,0.18)';
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLButtonElement).style.background = 'rgba(34,211,238,0.1)';
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path
            d="M7 1v12M1 7h12"
            stroke="#22d3ee"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
        <span className="hidden sm:inline">New Analysis</span>
      </button>
    </nav>
  );
}
