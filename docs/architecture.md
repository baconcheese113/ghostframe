# GhostFrame Architecture

## Overview

GhostFrame is a multi-frame variant impact scanner for cancer bioinformatics. It takes somatic mutations labeled "Silent" in standard annotations and re-examines each one across all 6 reading frames of the surrounding genomic region. A mutation that is silent in the canonical frame may be missense, stop-gained, or start-lost in an overlapping ORF — GhostFrame finds these hidden effects.

### Final product experience

A researcher uploads a MAF file, selects a reference FASTA (or runs the demo), and within seconds sees:

1. **Sankey diagram** — Silent → Missense / Stop-gain / Still-silent, by reading frame
2. **Interactive variant table** — frame-by-frame reclassification per variant, filterable/sortable
3. **3D Reading Frame Explorer** — single-variant drill-down: helix view with 6 frame ribbons, canonical vs. alternative effect highlighted side-by-side
4. **Embedded genome browser** (igv.js) — all 6 ORF tracks at the locus
5. **Neoantigen candidate panel** — MHC binding scores for reclassified variants
6. **Evidence badges** per ORF — scanning-only / OpenProt-confirmed / SynMICdb-scored
7. **LLM narrative panel** — plain-English explanation per variant citing computed artifacts (IC50, frame, domain overlap, SynMICdb score); always includes research disclaimer

The CLI (`ghostframe analyze`) serves as the power-user path. The FastAPI server backs the web UI. The core library stays framework-free (dataclasses only).

## Module map

| Subpackage | Purpose | Lane | Status |
|---|---|---|---|
| `orfs/` | 6-frame ORF scanning | Fast | Implemented |
| `variants/` | MAF/VCF parsing, filtering | Fast | Implemented |
| `seqfetch/` | Reference sequence retrieval | Fast | Implemented |
| `reclassify/` | Multi-frame reclassification | Fast | Stubbed |
| `peptides/` | 8-11mer mutant peptide generation | Deep | Implemented |
| `mhc/` | MHC binding prediction | Deep | Implemented |
| `domain/` | HMMER/Pfam domain annotation (EMBL-EBI API + local) | Deep | Planned |
| `evidence/` | OpenProt, SynMICdb, ClinVar linking | Deep | Implemented |
| `ranking/` | Candidate scoring and ranking | Deep | Planned |
| `explain/` | LLM narrative explanation + MCP server | Deep | Planned |
| `reports/` | Export (JSON, TSV) | Both | Stubbed |
| `pipeline/` | Fast/deep lane orchestration | Both | Stubbed |
| `cli/` | Click CLI entry points | N/A | Partial |

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
| EMBL-EBI HMMER | `domain/hmmer.py` (planned) | `https://www.ebi.ac.uk/Tools/hmmer/search/hmmscan` | None |
| EMBL-EBI InterPro | `domain/interproscan.py` (planned) | `https://www.ebi.ac.uk/interpro/api/` | None |
| NCBI E-utilities | `evidence/clinvar.py`, `seqfetch/remote.py` | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` | API key optional (10 req/s free) |
| Ensembl REST | `seqfetch/remote.py` | `https://rest.ensembl.org/` | None |
| Anthropic Claude | `explain/narrator.py` (planned) | `https://api.anthropic.com/` | `ANTHROPIC_API_KEY` required |

**Local/containerized tools (batch mode only, via Snakemake):**
- HMMER: `conda install -c bioconda hmmer` (activated by `GHOSTFRAME_HMMER_LOCAL=1`)
- InterProScan: BioContainers Singularity image — deferred; only for very large cohorts
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
