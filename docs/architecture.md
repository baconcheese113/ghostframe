# GhostFrame Architecture

## Overview

GhostFrame is a multi-frame variant impact scanner for cancer bioinformatics. It takes somatic mutations labeled "Silent" in standard annotations and re-examines each one across all 6 reading frames of the surrounding genomic region. A mutation that is silent in the canonical frame may be missense, stop-gained, or start-lost in an overlapping ORF — GhostFrame finds these hidden effects.

### Final product experience

A researcher uploads a MAF file, selects a reference FASTA (or runs the demo), and within seconds sees:

1. **Sankey diagram** — Silent → Missense / Stop-gain / Still-silent, by reading frame
2. **Interactive ORF-effect table** — one row per overlapping ORF effect, filterable/sortable, with streamed per-row enrichment state, compact evidence-tier circles, and sortable ClinVar / SynMICdb signals
3. **Reading Frame Explorer** — single-locus drill-down that keeps all six frames visible while strongly emphasizing the selected effect's frame, explicitly marking START / STOP codons, and clarifying that `*` denotes a stop codon
4. **Embedded genome browser** (igv.js) — all 6 ORF tracks at the locus
5. **Neoantigen candidate panel** — MHC binding scores for reclassified variants, explicitly labeled with the current HLA run allele
6. **Evidence badges** per ORF — scanning-only / OpenProt-confirmed / SynMICdb-scored
7. **LLM narrative panel** — plain-English explanation per variant citing computed artifacts (IC50, frame, domain overlap, SynMICdb score); always includes research disclaimer

The CLI (`ghostframe analyze`) serves as the power-user path. The FastAPI server backs the web UI. The core library stays framework-free (dataclasses only).

## Module map

| Subpackage | Purpose | Lane | Status |
|---|---|---|---|
| `orfs/` | 6-frame ORF scanning | Fast | Implemented |
| `variants/` | MAF/VCF parsing, filtering | Fast | Implemented |
| `seqfetch/` | Reference sequence retrieval | Fast | Implemented |
| `reclassify/` | Multi-frame reclassification | Fast | Implemented |
| `peptides/` | 8-11mer mutant peptide generation | Deep | Implemented |
| `mhc/` | MHC binding prediction | Deep | Implemented |
| `domain/` | HMMER/Pfam domain annotation via EMBL-EBI JDispatcher API | Deep | Implemented |
| `evidence/` | OpenProt, SynMICdb, ClinVar linking | Deep | Implemented |
| `ranking/` | Candidate scoring and ranking | Deep | Implemented |
| `explain/` | LLM narrative explanation + MCP server | Deep | Planned |
| `reports/` | Export (JSON, TSV) | Both | Implemented (TSV + JSON) |
| `pipeline/` | Fast/deep lane orchestration | Both | Implemented |
| `cli/` | Click CLI entry points | N/A | Partial |

Deep lane now runs as a streamed three-phase analysis:

1. Translate ORFs, generate peptides, and run one MHCflurry batch over the deduplicated peptide set
2. Run provider-aware lookups in parallel with separate pools for HMMER, OpenProt, ClinVar, and SynMICdb, scoring each variant as soon as its dependencies are ready
3. Rank the already-scored candidates after the final provider work completes

HMMER and OpenProt results are cached in-process for 24 hours. HMMER cache keys are SHA-256 hashes of translated proteins, and OpenProt cache keys are gene symbols.
The API streams heartbeat/progress events for the user-facing deep-analysis steps `Peptides`, `MHC Binding`, `Domain & Evidence`, and `Rank & Score`, and emits per-variant enrichment events before final ranking completes so long-running external lookups do not leave the frontend idle.
`fast_complete` also carries lightweight analysis metadata for the navbar label, and `enrich_complete` now distinguishes true binders from completed no-binder rows by sending nullable binding fields instead of synthetic zero-valued IC50s.
`fast_complete.summary` also carries structured count fields (`total_input_variants`, `total_silent_variants`, `total_orfs`, `total_effects`, `reclassified_effects`), and `running` events may include `progress_current` / `progress_total` so the frontend can render a determinate progress segment for `Domain & Evidence`.
Remote evidence providers are best-effort. Provider failures produce warning events and missing evidence for affected variants instead of terminating the full run.

## Pipeline flow

```
                         FAST LANE
    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ variants │───>│ seqfetch │───>│   orfs   │───>│reclassify│──> Summary
    │  (MAF)   │    │(ref seq) │    │(6-frame) │    │ (effect) │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                          │
                         DEEP LANE                        │
              ┌──────────┐    ┌──────────┐    ┌─────┴────┐
              │ peptides │───>│   mhc    │    │ evidence │
              │ (kmers)  │    │(binding) │    │ (links)  │
              └────┬─────┘    └────┬─────┘    └────┬─────┘
                   │              │               │
              ┌────▼──────────────▼───────────────▼─────┐
              │              domain/                     │
              │     (HMMER/Pfam via EMBL-EBI API)        │
              └─────────────────┬────────────────────────┘
                                │
                         ┌──────▼──────┐
                         │  ranking/   │──> ranked candidates
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │  explain/   │──> NarrativeExplanation
                         │  (Claude)   │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │  reports/   │──> JSON + TSV
                         └─────────────┘
```

## Consumption models

```
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
│Python Library│  │  FastAPI Server  │  │  orfs CLI    │  │  Snakemake   │
│import        │  │  ghostframe-api  │  │  (professor) │  │  workflow/   │
│ghostframe    │  │  calls library   │  │              │  │  batch runs  │
└──────┬───────┘  └────────┬─────────┘  └──────┬───────┘  └──────┬───────┘
       └──────────────────┬┘                   │                  │
                          │                   └──────────────────┘
                          │
              ┌───────────┴───────────┐
              │   ghostframe library  │
              │   packages/ghostframe │
              └───────────────────────┘
```

## Key design decisions

| Decision | Choice | Why |
|---|---|---|
| Package structure | uv workspace monorepo | Clean dep isolation between library and API |
| Core models | dataclasses | Lightweight, no framework dependency in core |
| API models | Pydantic | FastAPI integration, request validation |
| CLI | Click | Standard in bioinformatics |
| Python version | >= 3.13 | Oldest version still receiving bugfixes |
| Build backend | uv_build | Generated by uv, minimal config |

## Frontend tech stack

| Component | Library | Why |
|---|---|---|
| Framework | Next.js (App Router) | Already scaffolded; SSR for initial load |
| 3D visualization | react-three-fiber + @react-three/drei | React-native Three.js; 3D frame explorer is one self-contained component |
| Sankey + lollipop charts | D3.js | Bespoke SVG; no charting library handles these correctly |
| Data table | TanStack Table | Best-in-class filterable/sortable React table |
| Genome browser | igv.js | Drop-in embed, browser-native, no external server deps |
| Animations | Framer Motion | Summary card counters, page transitions |
| Styling | Tailwind CSS + shadcn/ui | Dark theme, component library |

3D (react-three-fiber) is reserved for the **3D Reading Frame Explorer** — a single-variant drill-down that renders the DNA window as a double helix with 6 frame ribbons. All other visualizations are polished 2D.

## Remote API dependencies

All external tools are accessed via free REST APIs for MVP and small cohorts. No Docker or local installation required for the core pipeline.

| Service | Used by | Endpoint | Auth |
|---|---|---|---|
| OpenProt 2.0 | `evidence/openprot.py` | `https://api.openprot.org/api/2.0/HS/` | None |
| EMBL-EBI HMMER JDispatcher | `domain/hmmer.py` | `https://www.ebi.ac.uk/Tools/services/rest/hmmer_hmmscan/` | None |
| NCBI E-utilities | `evidence/clinvar.py`, `seqfetch/remote.py` | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` | API key optional (3 req/s without key, 10 req/s with key) |
| Ensembl REST | `seqfetch/remote.py` | `https://rest.ensembl.org/` | None |
| Anthropic Claude | `explain/narrator.py` (planned) | `https://api.anthropic.com/` | `ANTHROPIC_API_KEY` required |

Deep-lane concurrency caps are intentionally provider-specific: HMMER uses up to 20 workers, OpenProt 5, and ClinVar 3. SynMICdb is a local dataset lookup and can run at a higher local concurrency. ClinVar requests are throttled inside the core client to match NCBI E-utilities guidance and retried with bounded backoff on transient failures such as `429`, `5xx`, and network timeouts.

**Local/containerized tools (batch mode only, via Snakemake):**
- HMMER: `conda install -c bioconda hmmer` — for future large-cohort Snakemake runs; not used by the core library
- NetMHCpan: custom Dockerfile required if added as a future `MHCPredictor` adapter

## Workflow layer (Snakemake)

For batch/cohort analysis, a Snakemake workflow in `workflow/` orchestrates the pipeline across multiple samples. The CLI handles single-sample runs; Snakemake handles GDC MAF download through cohort-level aggregation.

```
workflow/
  Snakefile               # main entry point
  rules/
    fetch_maf.smk         # download GDC MAF via API or manifest
    fast_lane.smk         # run ghostframe analyze per sample
    deep_lane.smk         # run deep lane per sample
    aggregate.smk         # cohort-level Sankey + stats
  config/
    config.yaml           # cohort ID, alleles, min_len, paths
    demo.yaml             # demo config (HPV16, ships with repo)
  envs/
    ghostframe.yaml       # conda env for ghostframe core
    hmmer.yaml            # conda env for local HMMER (batch mode)
```

Run modes:
```bash
snakemake demo --use-conda                     # HPV16 demo, no GDC download
snakemake --use-conda --cores 8                # single-cohort run
snakemake --use-conda --use-singularity -j 16  # with containerized tools
```

## ORF scanner details

The ORF scanner is the core implemented module. It:

1. **Parses FASTA** — `fasta.parse_file()` / `fasta.parse_text()` → `list[FastaRecord]`
2. **Scans 6 frames** — `scanner.find_orfs(sequence, min_length)` → `list[ORF]`
   - Frames 1-3: forward strand at offsets 0, 1, 2
   - Frames 4-6: reverse complement at offsets 0, 1, 2
3. **Maximal ORFs** — first ATG to first in-frame stop codon (TAA/TAG/TGA)
4. **Formats output** — `formatter.format_orf()` per assignment spec (codon spacing, 15 codons/line)

Position conventions:
- Forward frames: 1-based index from sequence start
- Reverse frames: negative index (rightmost base = -1)

## Test strategy

| Category | Markers | What |
|---|---|---|
| Golden tests | `@pytest.mark.golden` | Hand-computed ORF outputs, exact string equality |
| Unit tests | default | Individual module functions |
| Integration | `@pytest.mark.integration` | End-to-end pipeline, API endpoints |
| Slow | `@pytest.mark.slow` | MHC prediction, external evidence fetch |
