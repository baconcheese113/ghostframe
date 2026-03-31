'use client';

import { motion, AnimatePresence } from 'motion/react';
import type { DeepLaneEnrichment, FrameEffect } from '@/lib/types';
import EvidencePanel from './EvidencePanel';
import NeoantigensPanel from './NeoantigensPanel';
import NarrativePanel from './NarrativePanel';

interface DetailRowProps {
  variant: FrameEffect | null;
  enrichment?: DeepLaneEnrichment | null;
  isLoading?: boolean;
  hlaAlleles?: string[];
}

export default function DetailRow({
  variant,
  enrichment = null,
  isLoading = false,
  hlaAlleles = [],
}: DetailRowProps) {
  return (
    <AnimatePresence>
      {variant && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 16 }}
          transition={{ duration: 0.25 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-3"
        >
          <EvidencePanel variant={variant} enrichment={enrichment} isEnriching={isLoading && !enrichment} />
          <NeoantigensPanel
            variant={variant}
            enrichment={enrichment}
            isEnriching={isLoading && !enrichment}
            hlaAlleles={hlaAlleles}
          />
          <NarrativePanel variant={variant} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
