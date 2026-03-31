'use client';

export interface ApiStep {
  name: string;
  status: string;
  detail: string;
  elapsed_ms?: number;
}

const STEP_NAMES = [
  'MAF / FASTA',
  'Filter Silent',
  'Seq Fetch',
  '6-Frame ORF',
  'Reclassify',
  'Peptides',
  'MHC Binding',
  'Domain & Evidence',
  'Rank & Score',
];

const MOBILE_INDICES = [0, 3, 7, 8];

interface PipelineTraceProps {
  steps?: ApiStep[];
  runningStep?: string | null;
  runningDetail?: string | null;
  runningElapsedMs?: number | null;
  runningProgressCurrent?: number | null;
  runningProgressTotal?: number | null;
}

type ProgressState = {
  mode: 'idle' | 'indeterminate' | 'determinate' | 'complete';
  fillPercent: number;
  shimmerLeftPercent: number;
  shimmerWidthPercent: number;
};

function formatElapsedMs(elapsedMs?: number | null): string | null {
  if (elapsedMs === null || elapsedMs === undefined) return null;
  if (elapsedMs >= 60000) {
    const minutes = Math.floor(elapsedMs / 60000);
    const seconds = ((elapsedMs % 60000) / 1000).toFixed(1);
    return `${minutes}m ${seconds}s`;
  }
  return `${(elapsedMs / 1000).toFixed(2)}s`;
}

function isFinalStatus(status: string | undefined): boolean {
  return status === 'success' || status === 'skipped' || status === 'error' || status === 'not_implemented';
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function computeProgressState(opts: {
  steps?: ApiStep[];
  runningStep?: string | null;
  runningProgressCurrent?: number | null;
  runningProgressTotal?: number | null;
}): ProgressState {
  const stepMap = new Map(opts.steps?.map((step) => [step.name, step]));
  const segmentWidth = 100 / STEP_NAMES.length;
  const completedIndices = STEP_NAMES.filter((name) => isFinalStatus(stepMap.get(name)?.status));

  if (!opts.runningStep) {
    const fillPercent =
      completedIndices.length === STEP_NAMES.length
        ? 100
        : (completedIndices.length / STEP_NAMES.length) * 100;
    return {
      mode: completedIndices.length === STEP_NAMES.length ? 'complete' : 'idle',
      fillPercent,
      shimmerLeftPercent: fillPercent,
      shimmerWidthPercent: segmentWidth,
    };
  }

  const runningIndex = STEP_NAMES.indexOf(opts.runningStep);
  if (runningIndex === -1) {
    return {
      mode: 'idle',
      fillPercent: (completedIndices.length / STEP_NAMES.length) * 100,
      shimmerLeftPercent: 0,
      shimmerWidthPercent: segmentWidth,
    };
  }

  const completedBeforeRunning = STEP_NAMES.slice(0, runningIndex).filter((name) =>
    isFinalStatus(stepMap.get(name)?.status),
  ).length;
  const baseFillPercent = (completedBeforeRunning / STEP_NAMES.length) * 100;
  const hasNumericProgress =
    typeof opts.runningProgressCurrent === 'number' &&
    typeof opts.runningProgressTotal === 'number' &&
    opts.runningProgressTotal > 0;

  if (!hasNumericProgress) {
    return {
      mode: 'indeterminate',
      fillPercent: baseFillPercent,
      shimmerLeftPercent: baseFillPercent,
      shimmerWidthPercent: segmentWidth,
    };
  }

  const ratio = clamp(opts.runningProgressCurrent / opts.runningProgressTotal, 0, 1);
  return {
    mode: 'determinate',
    fillPercent: ((completedBeforeRunning + ratio) / STEP_NAMES.length) * 100,
    shimmerLeftPercent: baseFillPercent,
    shimmerWidthPercent: segmentWidth,
  };
}

export default function PipelineTrace({
  steps,
  runningStep,
  runningDetail,
  runningElapsedMs,
  runningProgressCurrent,
  runningProgressTotal,
}: PipelineTraceProps) {
  const stepMap = new Map(steps?.map((step) => [step.name, step]));
  const progressState = computeProgressState({
    steps,
    runningStep,
    runningProgressCurrent,
    runningProgressTotal,
  });

  const isRunning = Boolean(runningStep);
  const isComplete =
    !isRunning &&
    steps !== undefined &&
    steps.every((step) => step.status === 'success' || step.status === 'skipped');
  const isPartial =
    !isRunning &&
    steps !== undefined &&
    steps.some((step) => step.status === 'not_implemented' || step.status === 'error');

  return (
    <div data-testid="pipeline-trace" className="glass rounded-xl px-4 py-3 mx-4 sm:mx-0">
      <div className="hidden sm:flex items-center justify-between gap-1">
        {STEP_NAMES.map((name, index) => {
          const effectiveStep: ApiStep | undefined =
            stepMap.get(name) ??
            (runningStep === name ? { name, status: 'running', detail: '...' } : undefined);
          return (
            <PipelineStep
              key={name}
              label={name}
              apiStep={effectiveStep}
              isLast={index === STEP_NAMES.length - 1}
              index={index}
              revealDelay={index * 60}
            />
          );
        })}
      </div>

      <div className="grid grid-cols-4 gap-2 sm:hidden">
        {MOBILE_INDICES.map((index) => {
          const name = STEP_NAMES[index];
          const apiStep =
            stepMap.get(name) ??
            (runningStep === name ? { name, status: 'running', detail: '...' } : undefined);
          return (
            <div key={name} className="flex flex-col items-center gap-1">
              <StepDot apiStep={apiStep} />
              <span className="text-center text-[10px]" style={{ color: '#64748b' }}>
                {name}
              </span>
            </div>
          );
        })}
      </div>

      <div
        data-testid="pipeline-progress"
        data-progress-mode={progressState.mode}
        className="relative mt-3 h-1.5 overflow-hidden rounded-full"
        style={{
          background: 'rgba(30,41,59,0.8)',
          border: '1px solid rgba(34,211,238,0.08)',
        }}
      >
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-[width] duration-300"
          style={{
            width: `${progressState.fillPercent}%`,
            background:
              progressState.mode === 'complete'
                ? 'linear-gradient(90deg, rgba(34,211,238,0.9), rgba(74,222,128,0.85))'
                : 'linear-gradient(90deg, rgba(34,211,238,0.72), rgba(34,211,238,0.45))',
            boxShadow: '0 0 12px rgba(34,211,238,0.18)',
          }}
        />

        {progressState.mode === 'indeterminate' && (
          <div
            className="ghostframe-progress-shimmer absolute inset-y-0 rounded-full"
            style={{
              left: `${progressState.shimmerLeftPercent}%`,
              width: `${progressState.shimmerWidthPercent}%`,
              background:
                'linear-gradient(90deg, rgba(34,211,238,0.14), rgba(34,211,238,0.85), rgba(34,211,238,0.14))',
            }}
          />
        )}

        {Array.from({ length: STEP_NAMES.length - 1 }, (_, index) => (
          <div
            key={index}
            className="absolute inset-y-0 w-px"
            style={{
              left: `${((index + 1) / STEP_NAMES.length) * 100}%`,
              background: 'rgba(6,19,35,0.8)',
            }}
          />
        ))}
      </div>

      {steps !== undefined && (
        <div
          className="mt-2 text-right text-[10px] font-data"
          style={{
            color: isRunning
              ? '#22d3ee'
              : isComplete
                ? '#4ade80'
                : isPartial
                  ? '#fbbf24'
                  : '#ef4444',
          }}
        >
          {isRunning
            ? runningDetail ?? [runningStep, formatElapsedMs(runningElapsedMs)].filter(Boolean).join(' - ')
            : isComplete
              ? 'analysis complete'
              : isPartial
                ? 'partial results - see steps above'
                : 'pipeline error'}
        </div>
      )}

      <style jsx>{`
        .ghostframe-progress-shimmer {
          background-size: 200% 100%;
          animation: ghostframe-progress-shimmer 1.7s linear infinite;
        }

        @keyframes ghostframe-progress-shimmer {
          0% {
            transform: translateX(-40%);
            opacity: 0.4;
          }

          50% {
            opacity: 1;
          }

          100% {
            transform: translateX(40%);
            opacity: 0.4;
          }
        }
      `}</style>
    </div>
  );
}

function statusColors(status: string | undefined) {
  if (status === 'success') {
    return {
      bg: '#22d3ee18',
      border: '2px solid #22d3ee',
      shadow: '0 0 4px #22d3ee44',
      text: '#22d3ee',
    };
  }
  if (status === 'running') {
    return {
      bg: '#22d3ee08',
      border: '2px solid #22d3ee66',
      shadow: '0 0 8px #22d3ee44',
      text: '#22d3ee88',
    };
  }
  if (status === 'not_implemented') {
    return {
      bg: '#fbbf2418',
      border: '2px solid #fbbf24',
      shadow: '0 0 4px #fbbf2444',
      text: '#fbbf24',
    };
  }
  if (status === 'error') {
    return {
      bg: '#ef444418',
      border: '2px solid #ef4444',
      shadow: '0 0 4px #ef444444',
      text: '#ef4444',
    };
  }
  if (status === 'skipped') {
    return {
      bg: 'transparent',
      border: '1px solid #1e293b',
      shadow: 'none',
      text: '#334155',
    };
  }
  return {
    bg: '#0f172a',
    border: '1px solid #1e293b',
    shadow: 'none',
    text: '#334155',
  };
}

function StepIcon({ apiStep, index }: { apiStep?: ApiStep; index: number }) {
  const { text } = statusColors(apiStep?.status);
  if (apiStep?.status === 'running') {
    return (
      <span
        className="inline-block h-2 w-2 rounded-full animate-pulse"
        style={{ background: '#22d3ee' }}
      />
    );
  }
  if (apiStep?.status === 'success') {
    return (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <path
          d="M2 5l2.5 2.5L8 3"
          stroke={text}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }
  if (apiStep?.status === 'not_implemented') {
    return (
      <span className="text-[10px] font-data font-bold" style={{ color: text }}>
        !
      </span>
    );
  }
  if (apiStep?.status === 'error') {
    return (
      <span className="text-[10px] font-data font-bold" style={{ color: text }}>
        x
      </span>
    );
  }
  if (apiStep?.status === 'skipped') {
    return (
      <span className="text-[10px] font-data font-bold" style={{ color: text }}>
        -
      </span>
    );
  }
  return (
    <span className="text-[10px] font-data font-bold" style={{ color: text }}>
      {index + 1}
    </span>
  );
}

function StepDot({ apiStep }: { apiStep?: ApiStep }) {
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
      data-step-state={apiStep?.status ?? 'idle'}
    >
      <div className="flex flex-col items-center gap-1">
        <div
          className="h-7 w-7 rounded-full flex items-center justify-center transition-all duration-300"
          style={{ background: bg, border, boxShadow: shadow }}
        >
          <StepIcon apiStep={apiStep} index={index} />
        </div>
        <span className="text-xs font-data whitespace-nowrap" style={{ color: text }}>
          {label}
        </span>
        {apiStep && (
          <span
            className="text-[9px] font-data whitespace-nowrap max-w-[92px] truncate"
            style={{ color: '#334155' }}
            title={[apiStep.detail, formatElapsedMs(apiStep.elapsed_ms)].filter(Boolean).join(' - ')}
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
