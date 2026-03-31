'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingFn,
  type SortingState,
  useReactTable,
} from '@tanstack/react-table';
import type { DemoSummary, EffectType, FrameEffect, VariantProcessingStatus } from '@/lib/types';
import { FRAME_COLORS } from '@/lib/colors';
import EffectChip from '@/components/ui/EffectChip';
import EvidenceBadge from '@/components/ui/EvidenceBadge';
import SynmicdbScore from '@/components/ui/SynmicdbScore';

const col = createColumnHelper<FrameEffect>();
const RECLASSIFIED_ONLY = '__reclassified__';

const COLUMN_WIDTHS: Record<string, string> = {
  gene: '13.5rem',
  frame: '4rem',
  new_class: '6rem',
  aa_change: '5.5rem',
  evidence_tier: '6.75rem',
  synmicdb: '7.25rem',
  clinvar: '8.5rem',
  ic50: '5.75rem',
};

const EVIDENCE_SHORT_LABELS: Record<1 | 2 | 3, string> = {
  1: 'Scan',
  2: 'OpenProt',
  3: 'SynMIC',
};

function formatAaLabel(aa: string): string {
  return aa === '*' ? 'STOP' : aa;
}

function statusLabel(status: VariantProcessingStatus): string {
  if (status === 'enriching') return 'Enriching';
  if (status === 'scored') return 'Scored';
  if (status === 'no_binding') return 'No binder';
  return 'Scan-only';
}

function statusColor(status: VariantProcessingStatus): string {
  if (status === 'enriching') return '#22d3ee';
  if (status === 'scored') return '#4ade80';
  if (status === 'no_binding') return '#94a3b8';
  return '#475569';
}

function StatusDot({ status }: { status: VariantProcessingStatus }) {
  return (
    <span
      className={`inline-block h-1.5 w-1.5 rounded-full ${status === 'enriching' ? 'animate-pulse' : ''}`}
      style={{ background: statusColor(status), boxShadow: `0 0 6px ${statusColor(status)}44` }}
      title={statusLabel(status)}
    />
  );
}

function GeneCell({
  variant,
  status,
}: {
  variant: FrameEffect;
  status: VariantProcessingStatus;
}) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="inline-flex min-w-0 items-center gap-2">
        <StatusDot status={status} />
        <span className="truncate font-data font-medium" style={{ color: '#e2f3ff' }}>
          {variant.gene}
        </span>
        <span
          className="ml-auto shrink-0 text-[9px] font-data uppercase tracking-[0.16em]"
          style={{ color: statusColor(status) }}
        >
          {status === 'scored'
            ? 'Scored'
            : status === 'no_binding'
              ? 'No binder'
              : status === 'enriching'
                ? 'Live'
                : 'Scan'}
        </span>
      </span>
      <span className="truncate font-data text-[10px]" style={{ color: '#64748b' }}>
        chr {variant.chrom}:{variant.position}
      </span>
    </div>
  );
}

function EvidenceCell({ tier }: { tier: 1 | 2 | 3 }) {
  return (
    <span
      className="inline-flex items-center gap-1.5"
      title={
        tier === 3
          ? 'Tier 3 / SynMICdb support'
          : tier === 2
            ? 'Tier 2 / OpenProt support'
            : 'Tier 1 / Scan-only'
      }
    >
      <EvidenceBadge tier={tier} compact showLabel={false} />
      <span className="text-[10px] font-data" style={{ color: '#94a3b8' }}>
        {EVIDENCE_SHORT_LABELS[tier]}
      </span>
    </span>
  );
}

function ClinVarChip({ significance }: { significance: string | null | undefined }) {
  if (!significance) {
    return (
      <span className="text-[10px] font-data" style={{ color: '#475569' }}>
        --
      </span>
    );
  }

  return (
    <span
      className="inline-flex max-w-[10rem] items-center rounded-full px-2 py-0.5 text-[10px] font-data font-medium"
      style={{
        background: 'rgba(251,191,36,0.1)',
        border: '1px solid rgba(251,191,36,0.18)',
        color: '#fbbf24',
      }}
      title={significance}
    >
      <span className="truncate">{significance}</span>
    </span>
  );
}

function ic50DisplayValue(variant: FrameEffect): number {
  return variant.peptides.length > 0 ? variant.peptides[0].ic50 : Number.POSITIVE_INFINITY;
}

const clinvarSorting: SortingFn<FrameEffect> = (rowA, rowB) => {
  const a = rowA.original.clinvar_significance?.trim() ?? '';
  const b = rowB.original.clinvar_significance?.trim() ?? '';
  const aHas = a.length > 0 ? 1 : 0;
  const bHas = b.length > 0 ? 1 : 0;
  if (aHas !== bHas) {
    return aHas > bHas ? -1 : 1;
  }
  return a.localeCompare(b, undefined, { sensitivity: 'base' });
};

interface VariantTableProps {
  variants: FrameEffect[];
  variantStatuses: Record<string, VariantProcessingStatus>;
  selectedId: string | null;
  onSelect: (v: FrameEffect) => void;
  summary: DemoSummary;
  hlaLabel: string;
}

export default function VariantTable({
  variants,
  variantStatuses,
  selectedId,
  onSelect,
  summary,
  hlaLabel,
}: VariantTableProps) {
  const rowRefs = useRef<Record<string, HTMLTableRowElement | null>>({});
  const [sorting, setSorting] = useState<SortingState>([{ id: 'ic50', desc: false }]);
  const [searchTerm, setSearchTerm] = useState('');
  const [effectFilter, setEffectFilter] = useState(RECLASSIFIED_ONLY);

  useEffect(() => {
    if (variants.length === 0) {
      setSearchTerm('');
      setEffectFilter('');
      return;
    }
    setEffectFilter(RECLASSIFIED_ONLY);
    setSorting([{ id: 'ic50', desc: false }]);
  }, [variants]);

  useEffect(() => {
    if (!selectedId) {
      return;
    }

    rowRefs.current[selectedId]?.scrollIntoView({
      block: 'nearest',
      inline: 'nearest',
    });
  }, [selectedId]);

  const columns = useMemo(
    () => [
      col.accessor('gene', {
        id: 'gene',
        header: 'Gene',
        cell: (info) => {
          const status = variantStatuses[info.row.original.id] ?? 'scan_only';
          return <GeneCell variant={info.row.original} status={status} />;
        },
        sortingFn: (rowA, rowB) => {
          const byGene = rowA.original.gene.localeCompare(rowB.original.gene, undefined, {
            sensitivity: 'base',
          });
          return byGene !== 0 ? byGene : rowA.original.position - rowB.original.position;
        },
      }),
      col.accessor('frame', {
        header: 'Frame',
        cell: (info) => {
          const frame = info.getValue();
          return (
            <span
              className="inline-flex items-center justify-center h-5 w-6 rounded text-[10px] font-data font-bold"
              style={{
                background: `${FRAME_COLORS[frame]}22`,
                color: FRAME_COLORS[frame],
                border: `1px solid ${FRAME_COLORS[frame]}44`,
              }}
            >
              {frame}
            </span>
          );
        },
      }),
      col.accessor('new_class', {
        header: 'Effect',
        cell: (info) => <EffectChip effect={info.getValue()} small />,
      }),
      col.display({
        id: 'aa_change',
        header: 'AA',
        cell: (info) => (
          <span
            className="font-data text-xs"
            style={{ color: '#94a3b8' }}
            title={
              info.row.original.ref_aa === '*' || info.row.original.alt_aa === '*'
                ? '* denotes a stop codon'
                : undefined
            }
          >
            {formatAaLabel(info.row.original.ref_aa)}-{formatAaLabel(info.row.original.alt_aa)}
          </span>
        ),
        sortingFn: (rowA, rowB) =>
          `${formatAaLabel(rowA.original.ref_aa)}-${formatAaLabel(rowA.original.alt_aa)}`.localeCompare(
            `${formatAaLabel(rowB.original.ref_aa)}-${formatAaLabel(rowB.original.alt_aa)}`,
            undefined,
            { sensitivity: 'base' },
          ),
      }),
      col.accessor('evidence_tier', {
        header: 'Evidence',
        cell: (info) => <EvidenceCell tier={info.getValue()} />,
      }),
      col.accessor((row) => row.synmicdb_score ?? Number.NEGATIVE_INFINITY, {
        id: 'synmicdb',
        header: 'SynMICdb',
        cell: (info) => <SynmicdbScore score={info.row.original.synmicdb_score} compact />,
        sortingFn: 'basic',
        sortDescFirst: true,
      }),
      col.accessor((row) => row.clinvar_significance ?? null, {
        id: 'clinvar',
        header: 'ClinVar',
        cell: (info) => <ClinVarChip significance={info.getValue()} />,
        sortingFn: clinvarSorting,
      }),
      col.accessor(ic50DisplayValue, {
        id: 'ic50',
        header: 'IC50',
        cell: (info) => {
          const row = info.row.original;
          const status = variantStatuses[row.id] ?? 'scan_only';
          const value = info.getValue();

          if (!Number.isFinite(value)) {
            return (
              <span
                className="font-data text-xs"
                style={{ color: status === 'no_binding' ? '#94a3b8' : '#475569' }}
              >
                --
              </span>
            );
          }

          const color = value < 50 ? '#4ade80' : value < 500 ? '#fbbf24' : '#94a3b8';
          return (
            <span className="font-data text-xs font-medium" style={{ color }}>
              {value.toFixed(0)} nM
            </span>
          );
        },
        sortingFn: 'basic',
      }),
    ],
    [variantStatuses],
  );

  const effectOptions = useMemo(
    () => Array.from(new Set(variants.map((variant) => variant.new_class))) as EffectType[],
    [variants],
  );

  const filtered = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return variants.filter((variant) => {
      if (effectFilter === RECLASSIFIED_ONLY && variant.new_class === 'Silent') {
        return false;
      }
      if (effectFilter && effectFilter !== RECLASSIFIED_ONLY && variant.new_class !== effectFilter) {
        return false;
      }

      if (!normalizedSearch) {
        return true;
      }

      const searchable = [
        variant.gene,
        variant.chrom,
        String(variant.position),
        variant.new_class,
        `${variant.ref_aa}-${variant.alt_aa}`,
        variant.clinvar_significance ?? '',
      ]
        .join(' ')
        .toLowerCase();
      return searchable.includes(normalizedSearch);
    });
  }, [effectFilter, searchTerm, variants]);

  // eslint-disable-next-line react-hooks/incompatible-library -- TanStack Table manages this table instance internally.
  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const totalEffects = summary.total_effects || variants.length;

  return (
    <div className="glass rounded-xl overflow-hidden">
      <div
        className="flex flex-col gap-2 px-3 py-2.5 border-b"
        style={{ borderColor: 'rgba(34,211,238,0.1)' }}
      >
        <div className="flex flex-wrap items-center gap-2">
          <input
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Filter by gene, locus, effect"
            className="w-40 rounded-lg px-3 py-1.5 text-xs font-data outline-none sm:w-48"
            style={{
              background: 'rgba(34,211,238,0.06)',
              border: '1px solid rgba(34,211,238,0.18)',
              color: '#e2f3ff',
            }}
          />
          <select
            value={effectFilter}
            onChange={(event) => setEffectFilter(event.target.value)}
            className="rounded-lg px-3 py-1.5 text-xs font-data outline-none"
            style={{
              background: 'rgba(34,211,238,0.06)',
              border: '1px solid rgba(34,211,238,0.18)',
              color: '#94a3b8',
            }}
          >
            <option value={RECLASSIFIED_ONLY}>Reclassified only</option>
            <option value="">All effects</option>
            {effectOptions.map((effect) => (
              <option key={effect} value={effect}>
                {effect}
              </option>
            ))}
          </select>
          <span className="ml-auto text-xs font-data" style={{ color: '#475569' }}>
            {table.getRowModel().rows.length} of {totalEffects} ORF effects
          </span>
        </div>

        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <span
            data-testid="effect-row-helper"
            className="text-[10px] font-data"
            style={{ color: '#64748b' }}
          >
            Each row is an ORF effect. One silent variant can overlap multiple ORFs and produce
            multiple effect rows.
          </span>
          <span
            data-testid="variant-table-hla-note"
            className="text-[10px] font-data"
            style={{ color: '#64748b' }}
          >
            IC50 shown for {hlaLabel}
          </span>
        </div>
      </div>

      <div className="overflow-auto" data-testid="variant-table-scroll" style={{ maxHeight: '34rem' }}>
        <table className="w-full table-fixed text-xs" data-testid="variant-table">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} style={{ borderBottom: '1px solid rgba(34,211,238,0.1)' }}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="cursor-pointer select-none whitespace-nowrap px-2 py-1.5 text-left font-medium"
                    style={{
                      width: COLUMN_WIDTHS[header.column.id],
                      color: '#64748b',
                      background: 'rgba(6,19,35,0.92)',
                      backdropFilter: 'blur(12px)',
                      position: 'sticky',
                      top: 0,
                      zIndex: 2,
                    }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <span className="inline-flex max-w-full items-center gap-1 overflow-hidden text-ellipsis">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </span>
                    {header.column.getIsSorted() === 'asc'
                      ? ' ^'
                      : header.column.getIsSorted() === 'desc'
                        ? ' v'
                        : ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-10 text-center font-data text-xs" style={{ color: '#334155' }}>
                  Run an analysis to populate the ORF-effect table.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, index) => {
                const isSelected = row.original.id === selectedId;
                const status = variantStatuses[row.original.id] ?? 'scan_only';
                const rowBackground = isSelected
                  ? 'rgba(34,211,238,0.12)'
                  : status === 'enriching'
                    ? index % 2 === 0
                      ? 'rgba(5,28,42,0.78)'
                      : 'rgba(7,34,50,0.88)'
                    : status === 'scored'
                      ? index % 2 === 0
                        ? 'rgba(7,28,25,0.72)'
                        : 'rgba(8,34,30,0.82)'
                      : status === 'no_binding'
                        ? index % 2 === 0
                          ? 'rgba(15,23,42,0.72)'
                          : 'rgba(20,28,46,0.82)'
                        : index % 2 === 0
                          ? 'rgba(2,14,28,0.46)'
                          : 'rgba(4,19,37,0.66)';

                return (
                  <tr
                    key={row.id}
                    ref={(node) => {
                      rowRefs.current[row.original.id] = node;
                    }}
                    className="cursor-pointer transition-colors"
                    data-row-status={status}
                    style={{
                      borderBottom: '1px solid rgba(34,211,238,0.06)',
                      borderLeft: isSelected ? '2px solid #22d3ee' : '2px solid transparent',
                      background: rowBackground,
                      boxShadow: isSelected ? 'inset 0 0 0 1px rgba(34,211,238,0.14)' : 'none',
                    }}
                    onClick={() => onSelect(row.original)}
                    onMouseEnter={(event) => {
                      if (!isSelected) {
                        event.currentTarget.style.background = 'rgba(34,211,238,0.07)';
                      }
                    }}
                    onMouseLeave={(event) => {
                      if (!isSelected) {
                        event.currentTarget.style.background = rowBackground;
                      }
                    }}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="overflow-hidden whitespace-nowrap px-2 py-1.5 align-middle">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
