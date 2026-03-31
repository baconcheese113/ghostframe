---
title: GhostFrame
emoji: 👻
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# GhostFrame

A multi-frame variant impact scanner for cancer bioinformatics. GhostFrame re-examines "Silent" somatic mutations across all 6 reading frames to identify hidden non-synonymous effects in overlapping open reading frames (ORFs).

## What it does

A "Silent" mutation in standard cancer annotations means the canonical protein sequence is unchanged. But in regions where multiple ORFs overlap, the same nucleotide change may be missense or stop-gained in an alternative reading frame. GhostFrame scans all 6 frames, finds these hidden effects, and prioritizes the resulting mutant peptides as noncanonical neoantigen candidates.

**Output:** Interactive dashboard with streamed progress, a thin step progress bar, a compact ORF-effect table with sortable Gene / Evidence / ClinVar / SynMICdb signals, a selected-frame reading explorer that explicitly marks START and STOP codons, and MHC binding scores for the current HLA run allele (see [frontend/README.md](frontend/README.md)). Also exports JSON/TSV for downstream use.

> **Research/educational use only. Not for clinical decision-making.**

## Quickstart

```bash
# Install uv if you don't have it
# https://docs.astral.sh/uv/getting-started/installation/

# Clone and setup
git clone <repo-url>
cd ghostframe
uv sync

# Start the API server
uv run --package ghostframe-api uvicorn ghostframe_api.app:app --reload

# Start the Next.js frontend (in a separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:3000

# Run the ORF finder CLI on the HPV16 demo
uv run --package ghostframe orfs data/demo/hpv16_k02718.fasta --min-len 50

# Fetch a sequence region from a local FASTA (seqfetch)
uv run --package ghostframe python -c "
from ghostframe.seqfetch import local
print(local.fetch('K02718.1', 0, 100, 'data/demo/hpv16_k02718.fasta'))
"

# Reclassify a variant across all 6 reading frames
uv run --package ghostframe python -c "
from ghostframe.models import NormalizedVariant, GenomicWindow, ORF
from ghostframe.reclassify import engine, summary

window = GenomicWindow(chrom='chr1', start=0, end=9, sequence='ATGACGTTT')
orfs = [ORF(frame=1, pos=1, length=9, dna='ATGACGTTT')]
variant = NormalizedVariant(chrom='chr1', pos=4, ref='A', alt='T', classification='Silent', gene='DEMO')
effects = engine.reclassify(variant, orfs, window)
print(summary.aggregate(effects))
"

# Run the fast lane pipeline on the HPV16 demo MAF
uv run --package ghostframe ghostframe analyze data/demo/sample.maf --fasta data/demo/hpv16_k02718.fasta

# Annotate a protein sequence against Pfam via EMBL-EBI HMMER (domain module)
uv run --package ghostframe python -c "
from ghostframe.domain import hmmer
hits = hmmer.scan('MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSY')
for h in hits:
    print(f'{h.accession}  {h.name}  pos={h.start}-{h.end}  score={h.score:.1f}')
"

# Look up external evidence for a variant
uv run --package ghostframe python -c "
from ghostframe.models import NormalizedVariant
from ghostframe.evidence import clinvar, synmicdb
v = NormalizedVariant(chrom='17', pos=7675994, ref='G', alt='T', classification='Silent', gene='TP53')
print('SynMICdb:', synmicdb.lookup(v))
print('ClinVar:', clinvar.lookup(v))
"

# Reclassify a Silent variant across overlapping ORFs
uv run --package ghostframe python -c "
from ghostframe.models import GenomicWindow, NormalizedVariant, ORF
from ghostframe.reclassify import engine, summary

window = GenomicWindow(chrom='1', start=0, end=9, sequence='ATGAAATTT')
orf = ORF(frame=1, pos=1, length=9, dna='ATGAAATTT')
variant = NormalizedVariant(chrom='1', pos=4, ref='A', alt='G', classification='Silent', gene='TEST')

effects = engine.reclassify(variant, [orf], window)
for e in effects:
    print(f'Frame {e.orf.frame}: {e.old_class} -> {e.new_class} ({e.ref_aa}->{e.alt_aa})')

s = summary.aggregate(effects)
print('Counts:', s.counts_by_type)
print('Sankey:', s.sankey_data)
"

# Score and rank neoantigen candidates (ranking module)
uv run --package ghostframe python -c "
from ghostframe.models import BindingPrediction, DomainHit, EvidenceLookupResult, FrameEffect, ORF, Peptide, ScoredCandidate
from ghostframe.ranking import scorer, ranker

orf = ORF(frame=1, pos=1, length=30, dna='ATG' * 10)
effect = FrameEffect(orf=orf, old_class='Silent', new_class='Missense', ref_aa='A', alt_aa='V')
binding = BindingPrediction(peptide=Peptide(sequence='GILGFVFTL', start=0, k=9), allele='HLA-A*02:01', affinity=120.0, rank=1.5)
domain_hits = [DomainHit(accession='PF00071', name='Ras', start=5, end=39, score=42.0)]
evidence = EvidenceLookupResult(tier=3)

s = scorer.score(effect, binding, domain_hits, evidence)
candidates = ranker.rank([ScoredCandidate(effect=effect, binding=binding, domain_hits=domain_hits, evidence=evidence, score=s)])
print(f'Top candidate score: {candidates[0].score:.3f}')
"

# Run the deep lane pipeline on a FastLaneResult
uv run --package ghostframe python -c "
from ghostframe.models import FastLaneResult, FrameEffect, ORF, ReclassifySummary
from ghostframe.pipeline import deep_lane

orf = ORF(frame=1, pos=1, length=30, dna='ATG' + 'GCC' * 9 + 'TAA')
effect = FrameEffect(orf=orf, old_class='Silent', new_class='Missense', ref_aa='A', alt_aa='V', codon_pos=3)
fast_result = FastLaneResult(summary=ReclassifySummary(), sankey_data=[], reclassified_variants=[effect])
# NOTE: calls HMMER (remote) and MHCflurry (local) — may take ~2 min
result = deep_lane.run(fast_result, hla_alleles=['HLA-A*02:01'])
print(f'Ranked candidates: {len(result.ranked_candidates)}')
print(f'Top score: {result.ranked_candidates[0].score:.3f}')
"

# Run tests
uv run pytest
```

## Project layout

```
ghostframe/
  packages/
    ghostframe/           # Core Python library
      src/ghostframe/
        orfs/             # 6-frame ORF scanner (implemented)
        variants/         # MAF/VCF intake (implemented)
        seqfetch/         # Reference sequence retrieval (implemented)
        reclassify/       # Multi-frame reclassification (implemented)
        peptides/         # Kmer generation (implemented)
        mhc/              # MHC binding prediction (implemented)
        domain/           # Pfam domain annotation via EMBL-EBI HMMER (implemented)
        evidence/         # External evidence linking (implemented)
        ranking/          # Candidate scoring and ranking (implemented)
        reports/          # Output generation (TSV + JSON implemented)
        pipeline/         # Orchestration (fast lane + deep lane implemented)
        cli/              # CLI entry points
    ghostframe-api/       # FastAPI server
  tests/                  # Test suite (mirrors source structure)
  data/demo/              # Sample data and expected outputs
  docs/                   # Architecture documentation
  frontend/               # Next.js frontend — see frontend/README.md
```

## Pipeline architecture

GhostFrame uses a two-lane pipeline:

- **Fast Lane**: MAF intake -> filter Silent variants -> fetch reference sequence -> 6-frame ORF scan -> reclassify -> summary
- **Deep Lane**: Translate all reclassified ORFs -> generate peptides + run MHCflurry locally -> batch HMMER/OpenProt/ClinVar lookups in parallel -> candidate scoring/ranking -> report

Deep lane keeps 24-hour in-memory caches for HMMER domain scans and OpenProt gene lookups, so repeat analyses against the same inputs are effectively warm-started while the API process stays alive.
MHCflurry is run once per deep-analysis batch over the deduplicated peptide set, and the API now streams user-facing deep-analysis steps (`Peptides`, `MHC Binding`, `Domain & Evidence`, `Rank & Score`) plus per-variant enrichment events as soon as each variant is scoreable.
`fast_complete` now carries structured count metadata (`input variants -> silent variants -> ORFs -> ORF effects -> reclassified effects`) and `running` events can include numeric progress for `Domain & Evidence`, which drives the dashboard progress bar instead of relying on parsed text.
The dashboard navbar label is driven by streamed analysis metadata (sample barcode when uniquely available, otherwise filename or demo label), the current HLA allele is shown alongside IC50 outputs, and variants without a supported binder are rendered as explicit no-binder results instead of fake `0 nM` hits.
The ORF-effect table remains one row per overlapping ORF effect, but now uses a denser layout with restored tier-circle evidence cues and compact SynMICdb / ClinVar columns so large analyses stay scannable.
The reading-frame explorer keeps all six frames visible while explicitly labeling START / STOP codons and clarifying that `*` in amino-acid notation denotes a stop codon.
Remote providers are treated as best-effort enrichment: HMMER, OpenProt, ClinVar, or SynMICdb failures emit non-fatal warnings and continue with partial evidence instead of aborting the run. ClinVar requests are throttled to NCBI's published rate guidance and retried on transient failures such as `429` and `5xx`.

See [docs/architecture.md](docs/architecture.md) for details.

## Development

```bash
uv run pytest                    # run all tests
uv run pytest tests/orfs/        # run just ORF tests
uv run pytest -m golden          # run golden output tests
uv run ruff check .              # lint
uv run ruff format .             # format
uv run pyright                   # type check
cd frontend && npm run lint      # frontend lint
cd frontend && npm run knip      # frontend unused-code check
cd frontend && npm run build     # frontend production build
```

## Team

UMGC BIFS617 group project.

## License

MIT
