'use client';

import { useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import type { ApiWarning } from '@/lib/types';

interface AnalysisPanelProps {
  open: boolean;
  onToggle: () => void;
  onAnalyze: (opts: { mafContent: string | null; mafFilename: string | null }) => void;
  isLoading?: boolean;
  apiError?: string | null;
  warnings?: ApiWarning[];
}

export default function AnalysisPanel({
  open,
  onToggle,
  onAnalyze,
  isLoading = false,
  apiError = null,
  warnings = [],
}: AnalysisPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [mafContent, setMafContent] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [lineCount, setLineCount] = useState<number | null>(null);

  const accent = '#22d3ee';

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      setMafContent(text);
      setFileName(file.name);
      setLineCount(text.split('\n').filter((l) => l.trim() && !l.startsWith('#')).length);
    };
    reader.readAsText(file);
  }

  return (
    <div
      data-testid="analysis-panel"
      className="glass rounded-xl mx-4 sm:mx-0 overflow-hidden"
      style={{ borderColor: open ? 'rgba(34,211,238,0.25)' : 'rgba(34,211,238,0.1)' }}
    >
      {/* Collapsed bar */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 transition-colors cursor-pointer"
        style={{ height: 44, color: open ? accent : '#475569' }}
      >
        <div className="flex items-center gap-2">
          <span className="font-data text-[11px] font-bold" style={{ color: accent, opacity: open ? 1 : 0.5 }}>
            {open ? '-' : '+'}
          </span>
          <span className="font-display text-xs font-semibold">
            {open ? 'New Analysis' : 'Configure New Analysis'}
          </span>
        </div>
        {!open && (
          <span className="text-[10px] font-data" style={{ color: '#334155' }}>
            Upload MAF or use demo data
          </span>
        )}
      </button>

      {/* Expandable form */}
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="panel-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
          >
            <div className="px-4 pb-4 flex flex-col gap-3">
              {/* File upload */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] font-data" style={{ color: '#475569' }}>
                  MAF file
                </label>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="font-data text-[11px] px-3 py-2 rounded-lg text-left transition-all cursor-pointer"
                  style={{
                    background: 'rgba(2,14,28,0.7)',
                    border: '1px solid rgba(34,211,238,0.18)',
                    color: fileName ? '#e2f3ff' : '#475569',
                  }}
                >
                  {fileName ? fileName : 'Choose .maf or .txt file…'}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".maf,.txt"
                  className="hidden"
                  onChange={handleFileChange}
                />
                {lineCount !== null && (
                  <span className="text-[10px] font-data" style={{ color: '#334155' }}>
                    {lineCount} variant rows loaded
                  </span>
                )}
              </div>

              <div className="flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => onAnalyze({ mafContent: null, mafFilename: null })}
                  disabled={isLoading}
                  className="font-data text-[11px] px-3 py-1.5 rounded-lg transition-all cursor-pointer disabled:opacity-40"
                  style={{
                    background: 'rgba(34,211,238,0.05)',
                    border: '1px solid rgba(34,211,238,0.15)',
                    color: '#64748b',
                  }}
                >
                  Use Demo Data
                </button>
                <button
                  type="button"
                  onClick={() => onAnalyze({ mafContent, mafFilename: fileName })}
                  disabled={isLoading || mafContent === null}
                  className="font-display text-xs font-semibold px-4 py-1.5 rounded-lg transition-all cursor-pointer disabled:opacity-40"
                  style={{
                    background: 'rgba(34,211,238,0.12)',
                    border: '1px solid rgba(34,211,238,0.35)',
                    color: accent,
                  }}
                >
                  {isLoading ? 'Analyzing…' : 'Analyze →'}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {warnings.length > 0 && (
        <div
          className="mx-4 mb-3 text-[11px] font-data px-3 py-2 rounded-lg flex flex-col gap-1"
          style={{
            background: 'rgba(251,191,36,0.06)',
            border: '1px solid rgba(251,191,36,0.18)',
            color: '#cbd5e1',
          }}
        >
          <span style={{ color: '#fbbf24' }}>
            Warnings ({warnings.length})
          </span>
          {warnings.slice(0, 3).map((warning, index) => (
            <span key={`${warning.provider ?? 'provider'}-${warning.message ?? 'message'}-${index}`}>
              {(warning.provider ?? 'Provider').toUpperCase()}: {warning.message ?? 'Partial evidence unavailable.'}
            </span>
          ))}
          {warnings.length > 3 && (
            <span style={{ color: '#94a3b8' }}>
              +{warnings.length - 3} more warning(s)
            </span>
          )}
        </div>
      )}

      {apiError && (
        <div
          className="mx-4 mb-3 text-[11px] font-data px-3 py-2 rounded-lg"
          style={{
            background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.15)',
            color: '#94a3b8',
          }}
        >
          ⚠ {apiError}
        </div>
      )}
    </div>
  );
}
