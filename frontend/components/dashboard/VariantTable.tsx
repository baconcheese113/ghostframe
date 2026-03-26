'use client';

import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table';
import type { FrameEffect } from '@/lib/types';
import { FRAME_COLORS } from '@/lib/colors';
import EvidenceBadge from '@/components/ui/EvidenceBadge';
import EffectChip from '@/components/ui/EffectChip';

const col = createColumnHelper<FrameEffect>();

const columns = [
  col.accessor('gene', {
    header: 'Gene',
    cell: (i) => <span className="font-data font-medium" style={{ color: '#e2f3ff' }}>{i.getValue()}</span>,
  }),
  col.accessor('position', {
    header: 'Position',
    cell: (i) => <span className="font-data text-xs" style={{ color: '#94a3b8' }}>p.{i.getValue()}</span>,
  }),
  col.accessor('frame', {
    header: 'Frame',
    cell: (i) => {
      const f = i.getValue();
      return (
        <span
          className="inline-flex items-center justify-center h-5 w-6 rounded text-[10px] font-data font-bold"
          style={{ background: `${FRAME_COLORS[f]}22`, color: FRAME_COLORS[f], border: `1px solid ${FRAME_COLORS[f]}44` }}
        >
          {f}
        </span>
      );
    },
  }),
  col.accessor('new_class', {
    header: 'Effect',
    cell: (i) => <EffectChip effect={i.getValue()} small />,
  }),
  col.accessor('ref_aa', {
    id: 'aa_change',
    header: 'AA Change',
    cell: (i) => {
      const row = i.row.original;
      return (
        <span className="font-data text-xs" style={{ color: '#94a3b8' }}>
          {row.ref_aa}→{row.alt_aa}
        </span>
      );
    },
  }),
  col.accessor('evidence_tier', {
    header: 'Tier',
    cell: (i) => <EvidenceBadge tier={i.getValue()} />,
  }),
  col.accessor(
    (row) => row.peptides.length > 0 ? row.peptides[0].ic50 : 9999,
    {
      id: 'ic50',
      header: 'Best IC50',
      cell: (i) => {
        const val = i.getValue() as number;
        if (val >= 9999) return <span style={{ color: '#475569' }}>—</span>;
        const color = val < 50 ? '#4ade80' : val < 500 ? '#fbbf24' : '#475569';
        return <span className="font-data text-xs font-medium" style={{ color }}>{val} nM</span>;
      },
      sortingFn: 'basic',
    },
  ),
];

interface VariantTableProps {
  variants: FrameEffect[];
  selectedId: string | null;
  onSelect: (v: FrameEffect) => void;
}

export default function VariantTable({ variants, selectedId, onSelect }: VariantTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'ic50', desc: false }]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [effectFilter, setEffectFilter] = useState('');

  const filtered = useMemo(() => {
    let data = variants;
    if (effectFilter) data = data.filter((v) => v.new_class === effectFilter);
    return data;
  }, [variants, effectFilter]);

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const effects = Array.from(new Set(variants.map((v) => v.new_class)));

  return (
    <div className="glass rounded-xl overflow-hidden">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 px-4 py-3 border-b" style={{ borderColor: 'rgba(34,211,238,0.1)' }}>
        <input
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder="Filter by gene…"
          className="rounded-lg px-3 py-1.5 text-xs font-data outline-none w-36 sm:w-48"
          style={{
            background: 'rgba(34,211,238,0.06)',
            border: '1px solid rgba(34,211,238,0.18)',
            color: '#e2f3ff',
          }}
        />
        <select
          value={effectFilter}
          onChange={(e) => setEffectFilter(e.target.value)}
          className="rounded-lg px-3 py-1.5 text-xs font-data outline-none"
          style={{
            background: 'rgba(34,211,238,0.06)',
            border: '1px solid rgba(34,211,238,0.18)',
            color: '#94a3b8',
          }}
        >
          <option value="">All effects</option>
          {effects.map((e) => <option key={e} value={e}>{e}</option>)}
        </select>
        <span className="ml-auto text-xs font-data" style={{ color: '#475569' }}>
          {table.getRowModel().rows.length} of {variants.length}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto" data-testid="variant-table">
        <table className="w-full text-xs">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} style={{ borderBottom: '1px solid rgba(34,211,238,0.1)' }}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-3 py-2 text-left font-medium cursor-pointer select-none whitespace-nowrap"
                    style={{ color: '#475569', background: 'rgba(34,211,238,0.04)' }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() === 'asc' ? ' ↑' : header.column.getIsSorted() === 'desc' ? ' ↓' : ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center font-data text-xs" style={{ color: '#334155' }}>
                  Run an analysis to populate the variant table
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => {
                const isSelected = row.original.id === selectedId;
                return (
                  <tr
                    key={row.id}
                    className="cursor-pointer transition-colors"
                    style={{
                      borderBottom: '1px solid rgba(34,211,238,0.06)',
                      borderLeft: isSelected ? '2px solid #22d3ee' : '2px solid transparent',
                      background: isSelected ? 'rgba(34,211,238,0.05)' : 'transparent',
                    }}
                    onClick={() => onSelect(row.original)}
                    onMouseEnter={(e) => {
                      if (!isSelected) (e.currentTarget as HTMLTableRowElement).style.background = 'rgba(34,211,238,0.03)';
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) (e.currentTarget as HTMLTableRowElement).style.background = 'transparent';
                    }}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-3 py-2.5 whitespace-nowrap">
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
