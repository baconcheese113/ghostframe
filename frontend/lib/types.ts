export type EffectType = 'Missense' | 'Stop Gain' | 'Start Loss' | 'Silent';
export type VariantProcessingStatus = 'scan_only' | 'enriching' | 'scored' | 'no_binding';

export interface PeptidePrediction {
  sequence: string;
  allele: string;
  ic50: number;
  rank: number;
}

export interface FrameEffect {
  id: string;
  gene: string;
  position: number;
  frame: 1 | 2 | 3 | 4 | 5 | 6;
  old_class: 'Silent';
  new_class: EffectType;
  ref_codon: string;
  alt_codon: string;
  ref_aa: string;
  alt_aa: string;
  evidence_tier: 1 | 2 | 3;
  synmicdb_score: number | null;
  clinvar_significance?: string | null;
  narrative: string;
  peptides: PeptidePrediction[];
  // ORF track fields for ReadingFrameViewer
  orf_dna: string;
  orf_pos: number;
  orf_length: number;
  window_size: number;
  variant_in_window: number;
  codon_pos: number | null;
  chrom: string;
  ref: string;
  alt: string;
}

export interface DeepLaneCandidate {
  peptide_sequence: string | null;
  allele: string | null;
  ic50: number | null;
  rank: number | null;
  score: number;
  domain_hits: { accession: string; name: string; start: number; end: number; score: number }[];
}

export interface DeepLaneEnrichment {
  candidates: DeepLaneCandidate[];
  evidence: {
    tier: number;
    openprot_accession: string | null;
    openprot_type: string | null;
    synmicdb_score: number | null;
    clinvar_significance: string | null;
  };
}

export interface ApiWarning {
  provider: string | null;
  message: string | null;
  variant_id: string | null;
  fatal: boolean;
  elapsed_ms?: number;
}

export interface DemoSummary {
  total_input_variants: number;
  total_silent_variants: number;
  total_orfs: number;
  total_effects: number;
  reclassified_effects: number;
  total_silent: number;
  reclassified: number;
  frames_affected: number;
  best_ic50: number | null;
}

export interface AnalysisMeta {
  primary_label: string;
  secondary_label: string | null;
  sample_count: number;
  variant_count: number;
  is_demo: boolean;
  hla_alleles: string[];
}
