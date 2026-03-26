'use client';

import { useEffect, useRef, useState } from 'react';
import Script from 'next/script';

interface GenomeBrowserProps {
  locus: string;
}

export default function GenomeBrowser({ locus }: GenomeBrowserProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const browserRef = useRef<unknown>(null);
  const [igvReady, setIgvReady] = useState(false);

  // Mount browser once the igv script has loaded and the container is ready
  useEffect(() => {
    if (!igvReady || !containerRef.current) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const igv = (window as any).igv;
    if (typeof igv?.createBrowser !== 'function') return;

    let cancelled = false;
    igv
      .createBrowser(containerRef.current, {
        reference: {
          id: 'K02718.1',
          name: 'HPV16 / K02718.1',
          fastaURL: '/hpv16_k02718.fasta',
          indexURL: '/hpv16_k02718.fasta.fai',
        },
        locus,
        tracks: [],
      })
      .then((browser: unknown) => {
        if (!cancelled) browserRef.current = browser;
      })
      .catch(() => {/* silently ignore reference genome load failures */});

    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [igvReady]);

  // Navigate to new locus when prop changes
  useEffect(() => {
    if (!browserRef.current) return;
    (browserRef.current as { search: (l: string) => void }).search(locus);
  }, [locus]);

  return (
    <>
      {/* Load igv UMD from public/ — bypasses Turbopack bundling entirely,
          so the factory runs in the browser where document is available */}
      <Script src="/igv.min.js" strategy="afterInteractive" onLoad={() => setIgvReady(true)} />

      <div className="glass rounded-xl overflow-hidden">
        <div
          className="px-4 py-2 border-b flex items-center justify-between"
          style={{ borderColor: 'rgba(34,211,238,0.1)' }}
        >
          <span className="font-display text-xs font-semibold" style={{ color: '#22d3ee' }}>
            Genome Browser
          </span>
          <span className="font-data text-[10px]" style={{ color: '#475569' }}>
            {locus}
          </span>
        </div>
        <div
          ref={containerRef}
          style={{ minHeight: '120px', background: 'rgba(2,14,28,0.6)' }}
          className="igv-container"
        />
      </div>
    </>
  );
}
