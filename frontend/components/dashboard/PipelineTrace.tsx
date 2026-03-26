'use client';

export interface ApiStep {
  name: string;
  status: string;  // "success" | "error" | "not_implemented" | "skipped"
  detail: string;
}

const STEP_NAMES = [
  'MAF / FASTA',
  'Filter Silent',
  'Seq Fetch',
  '6-Frame ORF',
  'Reclassify',
  'Peptides',
  'MHC Binding',
  'Rank & Score',
];

const MOBILE_INDICES = [0, 3, 4, 7]; // MAF, 6-Frame ORF, Reclassify, Rank

interface PipelineTraceProps {
  steps?: ApiStep[];
}

export default function PipelineTrace({ steps }: PipelineTraceProps) {
  // Build a map for quick lookup; undefined steps = idle state
  const stepMap = new Map(steps?.map((s) => [s.name, s]));

  const isComplete = steps !== undefined && steps.every(
    (s) => s.status === 'success' || s.status === 'skipped'
  );
  const isPartial = steps !== undefined && steps.some(
    (s) => s.status === 'not_implemented' || s.status === 'error'
  );

  return (
    <div
      data-testid="pipeline-trace"
      className="glass rounded-xl px-4 py-3 mx-4 sm:mx-0"
    >
      {/* Desktop: horizontal row */}
      <div className="hidden sm:flex items-center justify-between gap-1">
        {STEP_NAMES.map((name, i) => (
          <PipelineStep
            key={i}
            label={name}
            apiStep={stepMap.get(name)}
            isLast={i === STEP_NAMES.length - 1}
            index={i}
            revealDelay={i * 60}
          />
        ))}
      </div>

      {/* Mobile: 4-up grid of key steps */}
      <div className="grid grid-cols-4 gap-2 sm:hidden">
        {MOBILE_INDICES.map((idx) => {
          const name = STEP_NAMES[idx];
          const apiStep = stepMap.get(name);
          return (
            <div key={idx} className="flex flex-col items-center gap-1">
              <StepDot apiStep={apiStep} index={idx} />
              <span className="text-center text-[10px]" style={{ color: '#64748b' }}>
                {name}
              </span>
            </div>
          );
        })}
      </div>

      {steps !== undefined && (
        <div className="mt-1 text-right text-[10px] font-data" style={{
          color: isComplete ? '#4ade80' : isPartial ? '#fbbf24' : '#ef4444',
        }}>
          {isComplete ? 'analysis complete ✓' : isPartial ? 'partial results — see steps above' : 'pipeline error'}
        </div>
      )}
    </div>
  );
}

function statusColors(status: string | undefined) {
  if (status === 'success') return { bg: '#22d3ee18', border: '2px solid #22d3ee', shadow: '0 0 4px #22d3ee44', text: '#22d3ee' };
  if (status === 'not_implemented') return { bg: '#fbbf2418', border: '2px solid #fbbf24', shadow: '0 0 4px #fbbf2444', text: '#fbbf24' };
  if (status === 'error') return { bg: '#ef444418', border: '2px solid #ef4444', shadow: '0 0 4px #ef444444', text: '#ef4444' };
  if (status === 'skipped') return { bg: 'transparent', border: '1px solid #1e293b', shadow: 'none', text: '#334155' };
  // idle
  return { bg: '#0f172a', border: '1px solid #1e293b', shadow: 'none', text: '#334155' };
}

function StepIcon({ apiStep, index }: { apiStep?: ApiStep; index: number }) {
  const { text } = statusColors(apiStep?.status);
  if (apiStep?.status === 'success') {
    return (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <path d="M2 5l2.5 2.5L8 3" stroke={text} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (apiStep?.status === 'not_implemented') return <span className="text-[10px] font-data font-bold" style={{ color: text }}>⚠</span>;
  if (apiStep?.status === 'error') return <span className="text-[10px] font-data font-bold" style={{ color: text }}>✕</span>;
  if (apiStep?.status === 'skipped') return <span className="text-[10px] font-data font-bold" style={{ color: text }}>—</span>;
  return <span className="text-[10px] font-data font-bold" style={{ color: text }}>{index + 1}</span>;
}

function StepDot({ apiStep }: { apiStep?: ApiStep; index: number }) {
  const { bg, border, shadow } = statusColors(apiStep?.status);
  return (
    <div
      className="h-3 w-3 rounded-full transition-all duration-300"
      style={{ background: bg, border, boxShadow: shadow }}
    />
  );
}

function PipelineStep({
  label,
  apiStep,
  isLast,
  index,
  revealDelay,
}: {
  label: string;
  apiStep?: ApiStep;
  isLast: boolean;
  index: number;
  revealDelay: number;
}) {
  const { bg, border, shadow, text } = statusColors(apiStep?.status);
  const hasResult = apiStep !== undefined;

  return (
    <div
      className="flex items-center gap-1 min-w-0"
      style={{
        opacity: hasResult ? 1 : 0.5,
        transition: `opacity 0.3s ease ${revealDelay}ms`,
      }}
      title={apiStep?.detail}
      data-step-status={apiStep?.status ?? 'idle'}
    >
      <div className="flex flex-col items-center gap-1">
        <div
          className="h-7 w-7 rounded-full flex items-center justify-center transition-all duration-300"
          style={{ background: bg, border, boxShadow: shadow }}
        >
          <StepIcon apiStep={apiStep} index={index} />
        </div>
        <span
          className="text-xs font-data whitespace-nowrap"
          style={{ color: text }}
        >
          {label}
        </span>
        {apiStep && (
          <span
            className="text-[9px] font-data whitespace-nowrap max-w-[80px] truncate"
            style={{ color: '#334155' }}
            title={apiStep.detail}
          >
            {apiStep.detail}
          </span>
        )}
      </div>
      {!isLast && (
        <div
          className="flex-1 h-px min-w-3 mb-[1.75rem] transition-all duration-300"
          style={{
            background: apiStep?.status === 'success' ? '#22d3ee60' : '#1e293b',
          }}
        />
      )}
    </div>
  );
}
