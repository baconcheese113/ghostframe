'use client';

import { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';

interface AnalysisPanelProps {
  open: boolean;
  onToggle: () => void;
  onAnalyze: (opts: {
    accession: string;
    rawSequence: string | null;
    inputType: 'accession' | 'sequence';
  }) => void;
  onLoadDemo: () => void;
  isLoading?: boolean;
  apiError?: string | null;
}

export default function AnalysisPanel({
  open,
  onToggle,
  onAnalyze,
  onLoadDemo,
  isLoading = false,
  apiError = null,
}: AnalysisPanelProps) {
  const [activeTab, setActiveTab] = useState<'accession' | 'sequence'>('accession');
  const [accession, setAccession] = useState('');
  const [rawSequence, setRawSequence] = useState('');
  const [seqError, setSeqError] = useState('');

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (activeTab === 'sequence' && rawSequence.trim() === '') {
      setSeqError('Paste a DNA sequence or FASTA block above');
      return;
    }
    setSeqError('');
    onAnalyze({
      accession: accession || 'K02718.1',
      rawSequence: activeTab === 'sequence' ? rawSequence : null,
      inputType: activeTab,
    });
  }

  const accent = '#22d3ee';
  const inputStyle: React.CSSProperties = {
    background: 'rgba(2,14,28,0.7)',
    border: '1px solid rgba(34,211,238,0.18)',
    borderRadius: 6,
    color: '#e2f3ff',
    padding: '6px 10px',
    fontSize: 13,
    fontFamily: 'JetBrains Mono, monospace',
    outline: 'none',
    width: '100%',
  };

  return (
    <div
      data-testid="analysis-panel"
      className="glass rounded-xl mx-4 sm:mx-0 overflow-hidden"
      style={{ borderColor: open ? 'rgba(34,211,238,0.25)' : 'rgba(34,211,238,0.1)' }}
    >
      {/* Collapsed bar — always visible */}
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 transition-colors cursor-pointer"
        style={{ height: 44, color: open ? accent : '#475569' }}
      >
        <div className="flex items-center gap-2">
          <span className="font-data text-[11px] font-bold" style={{ color: accent, opacity: open ? 1 : 0.5 }}>
            {open ? '−' : '+'}
          </span>
          <span className="font-display text-xs font-semibold">
            {open ? 'New Analysis' : 'Configure New Analysis'}
          </span>
        </div>
        {!open && (
          <span className="text-[10px] font-data" style={{ color: '#334155' }}>
            Enter accession or paste sequence
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
            <form onSubmit={handleSubmit} className="px-4 pb-4 flex flex-col gap-3">
              {/* Tab bar */}
              <div className="flex gap-0 border-b" style={{ borderColor: 'rgba(34,211,238,0.1)' }}>
                {(['accession', 'sequence'] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => { setActiveTab(tab); setSeqError(''); }}
                    className="font-data text-[11px] px-3 py-2 capitalize transition-colors cursor-pointer"
                    style={{
                      color: activeTab === tab ? accent : '#475569',
                      borderBottom: activeTab === tab ? `2px solid ${accent}` : '2px solid transparent',
                      marginBottom: -1,
                    }}
                  >
                    {tab === 'accession' ? 'Accession' : 'Sequence'}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              {activeTab === 'accession' && (
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-data" style={{ color: '#475569' }}>Accession ID</label>
                  <input
                    type="text"
                    placeholder="K02718.1"
                    value={accession}
                    onChange={(e) => setAccession(e.target.value)}
                    style={inputStyle}
                  />
                  <span className="text-[10px] font-data" style={{ color: '#334155' }}>
                    NCBI / GenBank accession — currently loads K02718.1 demo
                  </span>
                </div>
              )}

              {activeTab === 'sequence' && (
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-data" style={{ color: '#475569' }}>Paste sequence</label>
                  <textarea
                    rows={7}
                    placeholder={'>seq_id\nATCGATCGATCG...\n\nor just paste raw DNA'}
                    value={rawSequence}
                    onChange={(e) => { setRawSequence(e.target.value); setSeqError(''); }}
                    style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.5 }}
                  />
                  {seqError && (
                    <span className="text-[10px] font-data" style={{ color: '#ef4444' }}>
                      {seqError}
                    </span>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={onLoadDemo}
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
                  type="submit"
                  disabled={isLoading}
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
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error chip — always visible, outside the collapsible so it survives panel collapse */}
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
