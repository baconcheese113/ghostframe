'use client';

import { useState } from 'react';
import { NUCLEOTIDE_COLORS, FRAME_COLORS } from '@/lib/colors';

// ─── Nucleotide box ───────────────────────────────────────────────────────────

function NtBox({ nt, changed = false }: { nt: string; changed?: boolean }) {
  const color = NUCLEOTIDE_COLORS[nt] ?? '#64748b';
  return (
    <span
      className="inline-flex items-center justify-center rounded font-data font-bold text-[11px]"
      style={{
        width: 22, height: 22,
        background: changed ? `${color}55` : `${color}18`,
        border: `1.5px solid ${changed ? color : `${color}55`}`,
        color: changed ? '#fff' : color,
        boxShadow: changed ? `0 0 6px ${color}66` : 'none',
      }}
    >
      {nt}
    </span>
  );
}

// ─── Codon pair diagram ───────────────────────────────────────────────────────

function CodonPair({
  refCodon, altCodon, refAa, altAa, silent,
}: {
  refCodon: string; altCodon: string;
  refAa: string; altAa: string; silent: boolean;
}) {
  const changedIdx = refCodon.split('').findIndex((c, i) => c !== altCodon[i]);
  const effectColor = silent ? '#64748b' : '#fb923c';
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex flex-col items-center gap-1">
        <div className="flex gap-0.5">
          {refCodon.split('').map((nt, i) => <NtBox key={i} nt={nt} />)}
        </div>
        <span className="font-data text-[10px]" style={{ color: '#64748b' }}>{refCodon}</span>
      </div>
      <span className="font-data text-[14px]" style={{ color: '#475569' }}>→</span>
      <div className="flex flex-col items-center gap-1">
        <div className="flex gap-0.5">
          {altCodon.split('').map((nt, i) => <NtBox key={i} nt={nt} changed={i === changedIdx} />)}
        </div>
        <span className="font-data text-[10px]" style={{ color: '#64748b' }}>{altCodon}</span>
      </div>
      <div
        className="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg"
        style={{
          background: `${effectColor}14`,
          border: `1px solid ${effectColor}44`,
        }}
      >
        <span className="font-data font-bold text-sm" style={{ color: effectColor }}>
          {refAa} → {altAa}
        </span>
        <span className="font-data text-[10px]" style={{ color: effectColor }}>
          {silent ? 'Silent ✓' : 'Missense ✗'}
        </span>
      </div>
    </div>
  );
}

// ─── Frame comparison row ─────────────────────────────────────────────────────

function FrameRow({
  frameNum, direction, refCodon, altCodon, refAa, altAa, effect,
}: {
  frameNum: 1 | 4; direction: 'Fwd' | 'Rev';
  refCodon: string; altCodon: string;
  refAa: string; altAa: string;
  effect: 'Silent' | 'Missense';
}) {
  const frameColor = FRAME_COLORS[frameNum];
  const isSilent = effect === 'Silent';
  const effectColor = isSilent ? '#64748b' : '#fb923c';
  return (
    <div
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg flex-wrap"
      style={{
        background: isSilent ? 'rgba(100,116,139,0.06)' : 'rgba(251,146,60,0.06)',
        border: `1px solid ${isSilent ? 'rgba(100,116,139,0.18)' : 'rgba(251,146,60,0.25)'}`,
      }}
    >
      <div className="flex items-center gap-1.5 shrink-0" style={{ minWidth: 68 }}>
        <span
          className="inline-flex items-center justify-center rounded font-display font-bold text-[11px]"
          style={{
            width: 22, height: 22,
            background: `${frameColor}22`,
            border: `1.5px solid ${frameColor}55`,
            color: frameColor,
          }}
        >
          {frameNum}
        </span>
        <span className="font-data text-[10px]" style={{ color: frameColor }}>{direction}</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="flex gap-0.5">
          {refCodon.split('').map((nt, i) => <NtBox key={i} nt={nt} />)}
        </div>
        <span className="font-data text-[12px]" style={{ color: '#475569' }}>→</span>
        <div className="flex gap-0.5">
          {altCodon.split('').map((nt, i) => (
            <NtBox key={i} nt={nt} changed={refCodon[i] !== altCodon[i]} />
          ))}
        </div>
      </div>
      <span className="font-data font-bold text-sm" style={{ color: effectColor }}>
        {refAa} → {altAa}
      </span>
      <span
        className="ml-auto font-data text-[10px] px-2 py-0.5 rounded-full"
        style={{ background: `${effectColor}18`, border: `1px solid ${effectColor}44`, color: effectColor }}
      >
        {effect} {isSilent ? '✓' : '✗'}
      </span>
    </div>
  );
}

// ─── Neoantigen pipeline diagram ──────────────────────────────────────────────

const PIPELINE_STEPS = [
  { label: '"Silent"\nmutation',      color: '#64748b' },
  { label: 'Novel ORF\nin alt. frame', color: '#22d3ee' },
  { label: 'Peptide\nfragment',        color: '#60a5fa' },
  { label: 'MHC-I\npresentation',      color: '#c084fc' },
  { label: 'T-cell\nrecognition',      color: '#4ade80' },
] as const;

function PipelineDiagram() {
  return (
    <div className="flex items-center gap-1 flex-wrap justify-center">
      {PIPELINE_STEPS.map((step, i) => (
        <div key={step.label} className="flex items-center gap-1">
          <div
            className="px-2.5 py-1.5 rounded-lg text-center"
            style={{ background: `${step.color}12`, border: `1px solid ${step.color}44`, minWidth: 68 }}
          >
            {step.label.split('\n').map((line, j) => (
              <span key={j} className="block font-data text-[10px] leading-tight" style={{ color: step.color }}>
                {line}
              </span>
            ))}
          </div>
          {i < PIPELINE_STEPS.length - 1 && (
            <span className="font-data text-[12px]" style={{ color: '#334155' }}>→</span>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Quality gates ────────────────────────────────────────────────────────────

const GATES = [
  {
    n: 1, color: '#64748b',
    label: 'Silent variants only',
    body: 'Only mutations already labeled synonymous/silent in the canonical gene are analyzed. If a mutation already changes an amino acid in the main frame, it\'s already flagged — no need to check other frames.',
  },
  {
    n: 2, color: '#22d3ee',
    label: '6-frame ORF scan',
    body: 'A ±500 bp window around each silent variant is scanned in all 6 reading frames to find open reading frames (ATG → stop codon, minimum 50 amino acids). These are the candidate alternative proteins.',
  },
  {
    n: 3, color: '#fb923c',
    label: 'Reclassified effects',
    body: 'Each ORF overlapping the variant is re-evaluated. If the mutated codon changes the amino acid in that ORF, the variant is reclassified — Missense, Stop Gain, or Start Loss. Only these proceed to deep analysis.',
  },
  {
    n: 4, color: '#c084fc',
    label: 'MHC-I binding (IC50 / HLA)',
    body: 'Peptide fragments (8–11 aa) centered on the mutation are scored for binding affinity to HLA alleles using MHCflurry. IC50 is the binding strength — lower is stronger. Below 500 nM = potential immune target. HLA-A*02:01 used by default (~45% of global population).',
  },
  {
    n: 5, color: '#4ade80',
    label: 'Evidence corroboration',
    body: null as React.ReactNode,
  },
] as const;

const GATE_5_BODY = (
  <span>
    Three databases raise confidence:{' '}
    <strong style={{ color: '#60a5fa' }}>OpenProt</strong> confirms the ORF has been detected as a real protein in mass spec studies.{' '}
    <strong style={{ color: '#4ade80' }}>SynMICdb</strong> checks if this exact mutation has been seen in other cancer patients — recurrence is a strong signal.{' '}
    <strong style={{ color: '#f87171' }}>ClinVar</strong> flags germline clinical significance at the same position.
  </span>
);

// ─── Section card wrapper ─────────────────────────────────────────────────────

function SectionCard({
  num, title, accentColor, children, className = '',
}: {
  num: number; title: string; accentColor: string;
  children: React.ReactNode; className?: string;
}) {
  return (
    <section
      className={`glass rounded-xl px-4 py-5 flex flex-col gap-4 ${className}`}
      style={{ borderTop: `2px solid ${accentColor}55` }}
    >
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span
            className="inline-flex items-center justify-center rounded-full font-display font-bold text-[10px] shrink-0"
            style={{
              width: 20, height: 20,
              background: `${accentColor}22`,
              border: `1.5px solid ${accentColor}66`,
              color: accentColor,
            }}
          >
            {num}
          </span>
          <h2 className="font-display font-semibold text-sm" style={{ color: accentColor }}>
            {title}
          </h2>
        </div>
      </div>
      {children}
    </section>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function LandingExplainer() {
  const [wheelOpen, setWheelOpen] = useState(false);

  return (
    <>
      {/* Lightbox overlay */}
      {wheelOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(1,11,20,0.88)', backdropFilter: 'blur(8px)' }}
          onClick={() => setWheelOpen(false)}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/codon_wheel.png"
            alt="Codon wheel — full size"
            style={{
              maxWidth: '90vw',
              maxHeight: '90vh',
              borderRadius: 12,
              boxShadow: '0 0 60px rgba(34,211,238,0.2)',
              imageRendering: 'crisp-edges',
              cursor: 'zoom-out',
            }}
          />
          <span
            className="absolute top-4 right-5 font-data text-[11px]"
            style={{ color: '#64748b' }}
          >
            click anywhere to close
          </span>
        </div>
      )}

    <div data-testid="landing-explainer" className="flex flex-col gap-3">

      {/* ── Codon wheel — standalone hero, outside any card ────────────── */}
      <div className="flex flex-col lg:flex-row items-center gap-6 px-2 py-2">
        <button
          type="button"
          onClick={() => setWheelOpen(true)}
          className="shrink-0 relative group"
          aria-label="Click to zoom codon wheel"
          style={{ cursor: 'zoom-in' }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/codon_wheel.png"
            alt="Codon wheel — 64 DNA codons mapped to amino acids"
            className="rounded-xl w-[300px] h-[300px] lg:w-[480px] lg:h-[480px]"
            style={{ imageRendering: 'crisp-edges', display: 'block' }}
          />
          <span
            className="absolute bottom-2 right-2 font-data text-[9px] px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
            style={{ background: 'rgba(1,11,20,0.8)', color: '#22d3ee', border: '1px solid rgba(34,211,238,0.3)' }}
          >
            click to zoom
          </span>
        </button>

        <div className="flex flex-col gap-3 max-w-sm">
          <p className="font-display font-semibold text-sm" style={{ color: '#22d3ee' }}>
            The genetic code
          </p>
          <p className="font-data text-[11px] leading-relaxed" style={{ color: '#94a3b8' }}>
            DNA encodes proteins using 3-letter <strong style={{ color: '#d7f6ff' }}>codons</strong> — 64
            possible combinations that map to just 20 amino acids. The code is{' '}
            <strong style={{ color: '#d7f6ff' }}>deliberately redundant</strong>: multiple codons
            produce the same amino acid. Read inward from the outer ring.
          </p>
          <div
            className="rounded-lg px-3 py-2.5 text-[11px] font-data leading-relaxed"
            style={{ background: 'rgba(34,211,238,0.05)', border: '1px solid rgba(34,211,238,0.15)', color: '#94a3b8' }}
          >
            <strong style={{ color: '#22d3ee' }}>Key insight:</strong>{' '}
            Valine (V) is encoded by GTT, GTC, GTA, <em>and</em> GTG — four codons, same amino acid.
            A single nucleotide change can be completely invisible to the protein it encodes in one
            frame, while devastating in another.
          </div>
        </div>
      </div>

      {/* ── Cards 1–5: narrative grid ────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">

        {/* ── Card 2: Why "silent" mutations exist ─────────────────────── */}
        <SectionCard
          num={2}
          title="A change that changes nothing… in one frame"
          accentColor="#60a5fa"
        >
          <p className="font-data text-[11px] leading-relaxed" style={{ color: '#94a3b8' }}>
            When a tumor mutation changes a nucleotide, sequencing software checks if the
            new codon encodes the <strong style={{ color: '#d7f6ff' }}>same amino acid</strong>.
            If yes — labeled{' '}
            <strong style={{ color: '#64748b' }}>&ldquo;silent.&rdquo;</strong>{' '}
            No alarm. No follow-up.
          </p>
          <div className="flex flex-col gap-2">
            <span className="font-data text-[10px]" style={{ color: '#64748b' }}>
              Canonical frame (Frame 1):
            </span>
            <CodonPair
              refCodon="GTC" altCodon="GTT"
              refAa="Val" altAa="Val"
              silent
            />
            <p className="font-data text-[10px] leading-relaxed" style={{ color: '#64748b' }}>
              C→T at position 3. Both codons encode Valine. Standard pipelines stop here.
            </p>
          </div>
        </SectionCard>

        {/* ── Card 3: The blind spot ────────────────────────────────────── */}
        <SectionCard
          num={3}
          title="But the same DNA is read 6 ways"
          accentColor="#fb923c"
        >
          <p className="font-data text-[11px] leading-relaxed" style={{ color: '#94a3b8' }}>
            Your genome contains thousands of{' '}
            <strong style={{ color: '#d7f6ff' }}>overlapping genes</strong> — two proteins encoded
            in the same DNA, starting at different positions. The same mutation can land in a
            completely different codon in an overlapping frame and{' '}
            <strong style={{ color: '#fb923c' }}>change the amino acid</strong>.
          </p>
          <div className="flex flex-col gap-2">
            <span className="font-data text-[10px]" style={{ color: '#64748b' }}>
              Same mutation, two frames:
            </span>
            <FrameRow
              frameNum={1} direction="Fwd"
              refCodon="GTC" altCodon="GTT"
              refAa="Val" altAa="Val" effect="Silent"
            />
            <FrameRow
              frameNum={4} direction="Rev"
              refCodon="TCT" altCodon="TTT"
              refAa="Ser" altAa="Phe" effect="Missense"
            />
          </div>
          <div
            className="rounded-lg px-3 py-2 text-[10px] font-data"
            style={{ background: 'rgba(251,146,60,0.05)', border: '1px solid rgba(251,146,60,0.18)', color: '#94a3b8' }}
          >
            For decades, cancer genomics pipelines stopped at Frame 1. No standard tool
            systematically checked the other five.
          </div>
        </SectionCard>

        {/* ── Card 4: Why it matters for cancer ────────────────────────── */}
        <SectionCard
          num={4}
          title="Novel proteins = potential drug targets"
          accentColor="#4ade80"
        >
          <p className="font-data text-[11px] leading-relaxed" style={{ color: '#94a3b8' }}>
            Cancer cells display fragments of their proteins on the cell surface via{' '}
            <strong style={{ color: '#d7f6ff' }}>MHC class I</strong>.
            T-cells patrol for fragments they&apos;ve never seen — if they find one, they kill the cell.
          </p>
          <div
            className="rounded-lg px-3 py-2.5 flex flex-col gap-1.5"
            style={{ background: 'rgba(74,222,128,0.05)', border: '1px solid rgba(74,222,128,0.15)' }}
          >
            <span className="font-display font-semibold text-[11px]" style={{ color: '#4ade80' }}>
              The neoantigen opportunity
            </span>
            <p className="font-data text-[10px] leading-relaxed" style={{ color: '#94a3b8' }}>
              When a mutation creates a sequence the immune system has never seen, that fragment
              is called a <strong style={{ color: '#4ade80' }}>neoantigen</strong>. Because only
              cancer cells carry the mutation, a therapy targeting it{' '}
              <strong style={{ color: '#d7f6ff' }}>can&apos;t harm healthy tissue</strong>.
              And because the immune system has no prior tolerance to it, the T-cell response
              tends to be strong.
            </p>
          </div>
          <PipelineDiagram />
          <span className="font-data text-[10px]" style={{ color: '#64748b' }}>
            MHC-I binding affinity (IC50) determines how long the peptide is displayed.
            Lower IC50 = stronger binder = better target.
          </span>
        </SectionCard>

        {/* ── Card 5: The GhostFrame pipeline ──────────────────────────── */}
        <SectionCard
          num={5}
          title="The GhostFrame pipeline"
          accentColor="#c084fc"
        >
          <p className="font-data text-[11px] leading-relaxed" style={{ color: '#94a3b8' }}>
            Upload a tumor mutation file (MAF). GhostFrame runs these quality gates and
            reports only variants that survive each one.
          </p>
          <div className="flex flex-col gap-1.5">
            {GATES.map((gate) => (
              <div key={gate.n} className="flex gap-2.5">
                <span
                  className="inline-flex items-center justify-center rounded-full font-display font-bold text-[10px] shrink-0 mt-0.5"
                  style={{
                    width: 18, height: 18,
                    background: `${gate.color}22`,
                    border: `1.5px solid ${gate.color}66`,
                    color: gate.color,
                  }}
                >
                  {gate.n}
                </span>
                <div className="flex flex-col gap-0.5">
                  <span className="font-display font-semibold text-[10px]" style={{ color: gate.color }}>
                    {gate.label}
                  </span>
                  <span className="font-data text-[10px] leading-relaxed" style={{ color: '#94a3b8' }}>
                    {gate.n === 5 ? GATE_5_BODY : gate.body}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div
            className="rounded-lg px-2.5 py-2 text-[10px] font-data"
            style={{ background: 'rgba(192,132,252,0.04)', border: '1px solid rgba(192,132,252,0.14)', color: '#64748b' }}
          >
            Results appear ranked by score. Select any variant to see all 6 reading frames
            and the full evidence breakdown.
          </div>
        </SectionCard>

      </div>
    </div>
    </>
  );
}
