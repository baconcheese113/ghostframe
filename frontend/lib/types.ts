export type EffectType = 'Missense' | 'Stop Gain' | 'Start Loss' | 'Synonymous';

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
  narrative: string;
  peptides: PeptidePrediction[];
}

export interface SankeyNode {
  name: string;
}

export interface SankeyLink {
  source: number;
  target: number;
  value: number;
}

export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

export interface DemoSummary {
  total_silent: number;
  reclassified: number;
  frames_affected: number;
  best_ic50: number;
}
