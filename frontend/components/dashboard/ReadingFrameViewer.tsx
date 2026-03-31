'use client';

import { useEffect, useRef, useState } from 'react';
import type { FrameEffect } from '@/lib/types';
import { EFFECT_COLORS, FRAME_COLORS, NUCLEOTIDE_COLORS } from '@/lib/colors';

const CODON_TABLE: Record<string, string> = {
  TTT: 'F', TTC: 'F', TTA: 'L', TTG: 'L', CTT: 'L', CTC: 'L', CTA: 'L', CTG: 'L',
  ATT: 'I', ATC: 'I', ATA: 'I', ATG: 'M', GTT: 'V', GTC: 'V', GTA: 'V', GTG: 'V',
  TCT: 'S', TCC: 'S', TCA: 'S', TCG: 'S', CCT: 'P', CCC: 'P', CCA: 'P', CCG: 'P',
  ACT: 'T', ACC: 'T', ACA: 'T', ACG: 'T', GCT: 'A', GCC: 'A', GCA: 'A', GCG: 'A',
  TAT: 'Y', TAC: 'Y', TAA: '*', TAG: '*', CAT: 'H', CAC: 'H', CAA: 'Q', CAG: 'Q',
  AAT: 'N', AAC: 'N', AAA: 'K', AAG: 'K', GAT: 'D', GAC: 'D', GAA: 'E', GAG: 'E',
  TGT: 'C', TGC: 'C', TGA: '*', TGG: 'W', CGT: 'R', CGC: 'R', CGA: 'R', CGG: 'R',
  AGT: 'S', AGC: 'S', AGA: 'R', AGG: 'R', GGT: 'G', GGC: 'G', GGA: 'G', GGG: 'G',
};

interface CodonInfo {
  fwdStart: number;
  fwdEnd: number;
  codonStr: string;
  aa: string;
}

export interface ReadingFrameViewerProps {
  effects: FrameEffect[];
  windowSequence: string;
  variantRef: string;
  variantAlt: string;
  variantInWindow: number;
  selectedEffect?: FrameEffect | null;
}

const LABEL_W = 88;
const GENE_H = 30;
const DNA_H = 52;
const FRAME_H = 56;
const SUMMARY_H = 28;
const TOTAL_H = GENE_H + DNA_H + 6 * FRAME_H + SUMMARY_H;
const VISIBLE_NTS = 60;

function complement(nt: string): string {
  return ({ A: 'T', T: 'A', G: 'C', C: 'G', N: 'N' } as Record<string, string>)[nt.toUpperCase()] ?? 'N';
}

function reverseComplement(seq: string): string {
  return seq.split('').reverse().map(complement).join('');
}

function translate(codon: string): string {
  return CODON_TABLE[codon.toUpperCase()] ?? '?';
}

function aaColor(aa: string): string {
  if (aa === '*') return '#ef4444';
  if (aa === 'M') return '#22d3ee';
  if ('AVILMFWP'.includes(aa)) return '#60a5fa';
  if ('GSTCYNQ'.includes(aa)) return '#4ade80';
  if ('KRH'.includes(aa)) return '#f59e0b';
  if ('DE'.includes(aa)) return '#f87171';
  return '#94a3b8';
}

function getFrameCodons(fullSeq: string, frame: number): CodonInfo[] {
  const length = fullSeq.length;
  const codons: CodonInfo[] = [];

  if (frame <= 3) {
    const offset = frame - 1;
    for (let index = 0; offset + 3 * index + 2 < length; index++) {
      const start = offset + 3 * index;
      const codonStr = fullSeq.slice(start, start + 3).toUpperCase();
      codons.push({
        fwdStart: start,
        fwdEnd: start + 2,
        codonStr,
        aa: translate(codonStr),
      });
    }
    return codons;
  }

  const rcOffset = frame - 4;
  const rc = reverseComplement(fullSeq);
  for (let index = 0; rcOffset + 3 * index + 2 < length; index++) {
    const rcStart = rcOffset + 3 * index;
    const codonStr = rc.slice(rcStart, rcStart + 3).toUpperCase();
    const fwdStart = length - 3 - rcOffset - 3 * index;
    const fwdEnd = length - 1 - rcOffset - 3 * index;
    if (fwdStart < 0) continue;
    codons.push({
      fwdStart,
      fwdEnd,
      codonStr,
      aa: translate(codonStr),
    });
  }
  return codons;
}

function orfBounds(effect: FrameEffect): { start: number; end: number } {
  if (effect.frame <= 3) {
    return { start: effect.orf_pos - 1, end: effect.orf_pos - 1 + effect.orf_length - 1 };
  }

  const rcStart = Math.abs(effect.orf_pos) - 1;
  return {
    start: effect.window_size - rcStart - effect.orf_length,
    end: effect.window_size - 1 - rcStart,
  };
}

function orfTerminalCodons(effect: FrameEffect): {
  startCodonStart: number;
  stopCodonStart: number;
} {
  const bounds = orfBounds(effect);
  if (effect.frame <= 3) {
    return {
      startCodonStart: bounds.start,
      stopCodonStart: Math.max(bounds.start, bounds.end - 2),
    };
  }

  return {
    startCodonStart: Math.max(bounds.start, bounds.end - 2),
    stopCodonStart: bounds.start,
  };
}

function formatAaSymbol(aa: string): string {
  return aa === '*' ? 'STOP (*)' : aa;
}

function selectedEffectLabel(effect: FrameEffect | null | undefined): string {
  if (!effect) {
    return 'Selected effect: none';
  }
  return `Selected effect: Frame ${effect.frame} / ${effect.new_class} / ${formatAaSymbol(effect.ref_aa)}->${formatAaSymbol(effect.alt_aa)}`;
}

export default function ReadingFrameViewer({
  effects,
  windowSequence,
  variantRef,
  variantAlt,
  variantInWindow,
  selectedEffect = null,
}: ReadingFrameViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(800);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      setContainerWidth(entries[0].contentRect.width);
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  if (!windowSequence) {
    return (
      <div
        ref={containerRef}
        className="w-full flex items-center justify-center"
        style={{ minHeight: 200, color: '#64748b', fontSize: 14, fontFamily: 'monospace' }}
      >
        Select a variant to see the 6-frame reading analysis.
      </div>
    );
  }

  const visibleCount = Math.min(VISIBLE_NTS, windowSequence.length);
  const halfWindow = Math.floor(visibleCount / 2);
  const visibleStart = Math.max(
    0,
    Math.min(variantInWindow - halfWindow, windowSequence.length - visibleCount),
  );
  const visibleEnd = visibleStart + visibleCount;
  const visibleSequence = windowSequence.slice(visibleStart, visibleEnd);
  const variantColumn = variantInWindow - visibleStart;
  const ntWidth = (containerWidth - LABEL_W - 4) / visibleCount;

  const frameCodonMap = ([1, 2, 3, 4, 5, 6] as const).map((frame) =>
    getFrameCodons(windowSequence, frame).filter(
      (codon) => codon.fwdEnd >= visibleStart && codon.fwdStart < visibleEnd,
    ),
  );

  const effectsByFrame = new Map<number, FrameEffect>();
  for (const effect of effects) {
    if (!effectsByFrame.has(effect.frame)) {
      effectsByFrame.set(effect.frame, effect);
    }
  }
  if (selectedEffect) {
    effectsByFrame.set(selectedEffect.frame, selectedEffect);
  }

  const selectedFrame = selectedEffect?.frame ?? null;
  const geneLabel = selectedEffect?.gene ?? effects[0]?.gene ?? '';
  const positionLabel = selectedEffect
    ? `chr ${selectedEffect.chrom}:${selectedEffect.position}`
    : effects[0]
      ? `chr ${effects[0].chrom}:${effects[0].position}`
      : '';
  const framesWithOrfs = effectsByFrame.size;
  const framesReclassified = [...effectsByFrame.values()].filter(
    (effect) => effect.new_class !== 'Silent',
  ).length;

  function xOf(fwdPos: number): number {
    return LABEL_W + (fwdPos - visibleStart) * ntWidth;
  }

  function yOfFrame(frameIndex: number): number {
    return GENE_H + DNA_H + frameIndex * FRAME_H;
  }

  const variantHighlightX = LABEL_W + variantColumn * ntWidth;
  const variantHighlightVisible = variantColumn >= 0 && variantColumn < visibleCount;

  return (
    <div
      ref={containerRef}
      data-testid="reading-frame-viewer"
      data-selected-frame={selectedFrame ?? ''}
      className="w-full"
      style={{ minHeight: TOTAL_H }}
    >
      <div className="flex flex-wrap items-center justify-between gap-2 px-2 pt-1 pb-2">
        <div className="flex flex-col gap-1">
          <span
            data-testid="selected-effect-label"
            className="text-[11px] font-data"
            style={{ color: '#cbd5e1' }}
          >
            {selectedEffectLabel(selectedEffect)}
          </span>
          <span className="text-[10px] font-data" style={{ color: '#64748b' }}>
            Six-frame context stays visible; the selected frame is emphasized below.
          </span>
          <span className="text-[10px] font-data" style={{ color: '#475569' }}>
            START marks an ORF start codon, STOP marks an ORF terminator, and * in amino-acid
            labels also means stop codon.
          </span>
        </div>
        {selectedFrame && (
          <span
            data-testid="selected-effect-badge"
            className="inline-flex items-center rounded-full px-3 py-1 text-[10px] font-data"
            style={{
              color: FRAME_COLORS[selectedFrame],
              background: `${FRAME_COLORS[selectedFrame]}18`,
              border: `1px solid ${FRAME_COLORS[selectedFrame]}44`,
            }}
          >
            Frame {selectedFrame} focus
          </span>
        )}
      </div>

      <svg
        width={containerWidth}
        height={TOTAL_H}
        style={{ fontFamily: "'JetBrains Mono', monospace", display: 'block' }}
      >
        <g>
          <line x1={LABEL_W} y1={14} x2={containerWidth - 4} y2={14} stroke="#334155" strokeWidth={1.5} />
          <rect
            x={LABEL_W + visibleCount * 0.3 * ntWidth}
            y={8}
            width={visibleCount * 0.4 * ntWidth}
            height={12}
            fill="#22d3ee14"
            stroke="#22d3ee40"
            strokeWidth={1}
            rx={2}
          />
          <text x={LABEL_W + 2} y={12} fill="#475569" fontSize={9}>
            {"5'"}
          </text>
          <text x={containerWidth - 8} y={12} fill="#475569" fontSize={9} textAnchor="end">
            {"3'"}
          </text>
          <text
            x={LABEL_W + visibleCount * 0.5 * ntWidth}
            y={11}
            fill="#22d3ee88"
            fontSize={8}
            textAnchor="middle"
          >
            window
          </text>
          {geneLabel && (
            <text
              x={LABEL_W - 4}
              y={18}
              fill="#64748b"
              fontSize={10}
              textAnchor="end"
              fontFamily="monospace"
            >
              {geneLabel}
            </text>
          )}
          {positionLabel && (
            <text x={containerWidth - 4} y={26} fill="#475569" fontSize={9} textAnchor="end">
              {positionLabel}
            </text>
          )}
        </g>

        {variantHighlightVisible && (
          <rect
            x={variantHighlightX}
            y={GENE_H + 2}
            width={ntWidth}
            height={DNA_H + 6 * FRAME_H - 4}
            fill="#fbbf2412"
            stroke="#fbbf2438"
            strokeWidth={1}
          />
        )}

        <g transform={`translate(0, ${GENE_H})`}>
          <text x={LABEL_W - 4} y={17} fill="#64748b" fontSize={9} textAnchor="end">
            {"5'->3'"}
          </text>
          <text x={LABEL_W - 4} y={38} fill="#475569" fontSize={8} textAnchor="end">
            {"3'<-5'"}
          </text>

          {visibleSequence.split('').map((rawNt, index) => {
            const nt = rawNt.toUpperCase();
            const comp = complement(nt);
            const isVariantNt = index === variantColumn;
            const ntColor = NUCLEOTIDE_COLORS[nt] ?? '#64748b';

            return (
              <g key={index} transform={`translate(${LABEL_W + index * ntWidth}, 4)`}>
                {isVariantNt && (
                  <text x={ntWidth / 2} y={-3} textAnchor="middle" fontSize={8} fill="#fbbf24">
                    {`${variantRef}->${variantAlt}`}
                  </text>
                )}
                <rect
                  x={0}
                  y={0}
                  width={ntWidth - 1}
                  height={19}
                  rx={2}
                  fill={isVariantNt ? ntColor : `${ntColor}28`}
                  stroke={ntColor}
                  strokeWidth={isVariantNt ? 1.5 : 0.4}
                  strokeOpacity={isVariantNt ? 0.9 : 0.5}
                />
                {ntWidth > 7 && (
                  <text
                    x={ntWidth / 2}
                    y={14}
                    textAnchor="middle"
                    fontSize={Math.min(12, ntWidth - 2)}
                    fill={isVariantNt ? '#0f172a' : ntColor}
                    fontWeight={isVariantNt ? 'bold' : 'normal'}
                  >
                    {nt}
                  </text>
                )}
                {ntWidth > 9 && (
                  <text
                    x={ntWidth / 2}
                    y={35}
                    textAnchor="middle"
                    fontSize={Math.min(9, ntWidth - 3)}
                    fill="#475569"
                  >
                    {comp}
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {([1, 2, 3, 4, 5, 6] as const).map((frame, frameIndex) => {
          const frameColor = FRAME_COLORS[frame] ?? '#94a3b8';
          const isReverse = frame >= 4;
          const yBase = yOfFrame(frameIndex);
          const codons = frameCodonMap[frameIndex];
          const frameEffect = effectsByFrame.get(frame);
          const bounds = frameEffect ? orfBounds(frameEffect) : null;
          const terminals = frameEffect ? orfTerminalCodons(frameEffect) : null;
          const isSelectedFrame = selectedFrame === frame;
          const hasFrameFocus = selectedFrame !== null;

          return (
            <g
              key={frame}
              transform={`translate(0, ${yBase})`}
              opacity={hasFrameFocus && !isSelectedFrame ? 0.48 : 1}
            >
              <line x1={0} y1={0} x2={containerWidth} y2={0} stroke="#1e293b" strokeWidth={1} />

              {isSelectedFrame && (
                <rect
                  x={0}
                  y={2}
                  width={containerWidth}
                  height={FRAME_H - 4}
                  fill={`${frameColor}12`}
                  stroke={`${frameColor}40`}
                  strokeWidth={1}
                  rx={6}
                />
              )}

              <text x={6} y={32} fill={frameColor} fontSize={10} fontFamily="monospace">
                {isReverse ? '<' : '>'} Frame {frame}
              </text>

              {bounds && bounds.start >= 0 && (() => {
                const x1 = Math.max(LABEL_W, xOf(bounds.start));
                const x2 = Math.min(containerWidth - 2, xOf(bounds.end + 1));
                if (x2 <= x1) return null;

                return (
                  <rect
                    x={x1}
                    y={10}
                    width={x2 - x1}
                    height={34}
                    fill={isSelectedFrame ? `${frameColor}24` : `${frameColor}14`}
                    stroke={isSelectedFrame ? `${frameColor}88` : 'none'}
                    strokeWidth={isSelectedFrame ? 1.2 : 0}
                    rx={3}
                  />
                );
              })()}

              {codons.map((codon, codonIndex) => {
                const x = xOf(codon.fwdStart);
                const width = 3 * ntWidth - 1;
                if (width < 1) return null;

                const isVariantCodon =
                  variantInWindow >= codon.fwdStart && variantInWindow <= codon.fwdEnd;
                const variantEffect = isVariantCodon ? frameEffect : undefined;
                const effectColor = variantEffect
                  ? EFFECT_COLORS[variantEffect.new_class] ?? '#fbbf24'
                  : null;
                const isOrfStartCodon =
                  terminals !== null && codon.fwdStart === terminals.startCodonStart;
                const isOrfStopCodon =
                  terminals !== null && codon.fwdStart === terminals.stopCodonStart;
                const isStartLoss = isVariantCodon && variantEffect?.new_class === 'Start Loss';
                const isStopGain = isVariantCodon && variantEffect?.new_class === 'Stop Gain';

                const baseAaColor = aaColor(codon.aa);
                const boxFill = isStartLoss
                  ? 'rgba(192,132,252,0.28)'
                  : isStopGain
                    ? 'rgba(248,113,113,0.28)'
                    : effectColor
                      ? `${effectColor}30`
                      : `${baseAaColor}20`;
                const boxStroke = isStartLoss
                  ? '#c084fc'
                  : isStopGain
                    ? '#f87171'
                    : effectColor ?? `${baseAaColor}55`;
                const boxStrokeWidth = isSelectedFrame && isVariantCodon ? 1.9 : effectColor ? 1.5 : 0.5;
                const labelColor = effectColor ?? baseAaColor;
                const codonLabel = isStartLoss
                  ? 'START LOST'
                  : isStopGain
                    ? 'STOP GAIN'
                    : isSelectedFrame && isOrfStartCodon
                      ? 'START'
                      : isSelectedFrame && isOrfStopCodon
                        ? 'STOP'
                        : variantEffect && variantEffect.new_class !== 'Silent' && isVariantCodon
                          ? `${variantEffect.ref_aa}->${variantEffect.alt_aa === '*' ? 'STOP' : variantEffect.alt_aa}`
                          : null;

                return (
                  <g key={codonIndex}>
                    {(isOrfStartCodon || isOrfStopCodon) && (
                      <line
                        x1={x + width / 2}
                        y1={10}
                        x2={x + width / 2}
                        y2={14}
                        stroke={isOrfStartCodon ? '#22d3ee' : '#ef4444'}
                        strokeWidth={1.1}
                      />
                    )}

                    <rect
                      x={x}
                      y={12}
                      width={width}
                      height={28}
                      rx={2}
                      fill={boxFill}
                      stroke={boxStroke}
                      strokeWidth={boxStrokeWidth}
                    />

                    {isSelectedFrame && isVariantCodon && (
                      <rect
                        x={x - 1}
                        y={11}
                        width={width + 2}
                        height={30}
                        rx={3}
                        fill="none"
                        stroke="#fbbf24"
                        strokeWidth={1.2}
                      />
                    )}

                    {codonLabel && (
                      <text
                        x={x + width / 2}
                        y={10}
                        textAnchor="middle"
                        fontSize={isStartLoss || isStopGain ? 8 : 7}
                        fill={
                          isStartLoss
                            ? '#c084fc'
                            : isStopGain
                              ? '#f87171'
                              : isOrfStartCodon
                                ? '#22d3ee'
                                : isOrfStopCodon
                                  ? '#ef4444'
                                  : effectColor ?? '#fbbf24'
                        }
                        fontWeight={isSelectedFrame ? 'bold' : 'normal'}
                      >
                        {codonLabel}
                      </text>
                    )}

                    {width > 8 && (
                      <text
                        x={x + width / 2}
                        y={30}
                        textAnchor="middle"
                        fontSize={Math.min(13, width - 4)}
                        fill={labelColor}
                          fontWeight={isSelectedFrame ? 'bold' : 'normal'}
                      >
                        {codon.aa}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          );
        })}

        <g transform={`translate(0, ${GENE_H + DNA_H + 6 * FRAME_H + 6})`}>
          <line x1={LABEL_W} y1={0} x2={containerWidth} y2={0} stroke="#1e293b" strokeWidth={1} />
          <text x={LABEL_W} y={16} fill="#64748b" fontSize={10}>
            {geneLabel ? `${geneLabel} / ` : ''}
            {framesWithOrfs} frame{framesWithOrfs !== 1 ? 's' : ''} with ORFs / {framesReclassified}{' '}
            reclassified
          </text>
        </g>
      </svg>
    </div>
  );
}
