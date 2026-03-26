'use client';

import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { sankey, sankeyLinkHorizontal } from 'd3-sankey';
import type { SankeyData } from '@/lib/types';
import { EFFECT_COLORS } from '@/lib/colors';

interface SankeyChartProps {
  data: SankeyData;
}

const NODE_COLORS: Record<string, string> = {
  'Silent Variants': '#22d3ee',
  'Still Silent': '#475569',
  Missense: EFFECT_COLORS['Missense'],
  'Stop Gain': EFFECT_COLORS['Stop Gain'],
  'Start Loss': EFFECT_COLORS['Start Loss'],
};

export default function SankeyChart({ data }: SankeyChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const el = svgRef.current;
    const container = containerRef.current;

    const W = container.clientWidth || 340;
    const H = container.clientHeight || 260;
    const margin = { top: 16, right: 100, bottom: 16, left: 80 };

    d3.select(el).selectAll('*').remove();
    el.setAttribute('width', String(W));
    el.setAttribute('height', String(H));

    const layout = sankey<{ name: string }, object>()
      .nodeWidth(12)
      .nodePadding(18)
      .extent([
        [margin.left, margin.top],
        [W - margin.right, H - margin.bottom],
      ]);

    const graph = layout({
      nodes: data.nodes.map((d) => ({ ...d })),
      links: data.links.map((d) => ({ ...d })),
    });

    const svg = d3.select(el);

    // Draw links
    svg
      .append('g')
      .selectAll('path')
      .data(graph.links)
      .join('path')
      .attr('d', sankeyLinkHorizontal())
      .attr('fill', 'none')
      .attr('stroke', (d) => {
        const target = d.target as { name: string };
        return NODE_COLORS[target.name] ?? '#475569';
      })
      .attr('stroke-opacity', 0.22)
      .attr('stroke-width', (d) => Math.max(1, d.width ?? 1))
      .attr('data-testid', 'sankey-link');

    // Draw nodes
    svg
      .append('g')
      .selectAll('rect')
      .data(graph.nodes)
      .join('rect')
      .attr('x', (d) => d.x0 ?? 0)
      .attr('y', (d) => d.y0 ?? 0)
      .attr('width', (d) => (d.x1 ?? 0) - (d.x0 ?? 0))
      .attr('height', (d) => Math.max(1, (d.y1 ?? 0) - (d.y0 ?? 0)))
      .attr('fill', (d) => NODE_COLORS[d.name] ?? '#475569')
      .attr('rx', 3)
      .style('filter', (d) => `drop-shadow(0 0 4px ${NODE_COLORS[d.name] ?? '#475569'}88)`);

    // Node labels
    svg
      .append('g')
      .selectAll('text')
      .data(graph.nodes)
      .join('text')
      .attr('x', (d) => ((d.x0 ?? 0) < W / 2 ? (d.x1 ?? 0) + 8 : (d.x0 ?? 0) - 8))
      .attr('y', (d) => ((d.y1 ?? 0) + (d.y0 ?? 0)) / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', (d) => ((d.x0 ?? 0) < W / 2 ? 'start' : 'end'))
      .attr('fill', (d) => NODE_COLORS[d.name] ?? '#94a3b8')
      .attr('font-size', '11px')
      .attr('font-family', "'JetBrains Mono', monospace")
      .text((d) => `${d.name} (${d.value})`);
  }, [data]);

  return (
    <div ref={containerRef} className="w-full h-full" style={{ minHeight: '220px' }}>
      <svg
        ref={svgRef}
        data-testid="sankey-chart"
        className="w-full h-full"
        style={{ overflow: 'visible' }}
      />
    </div>
  );
}
