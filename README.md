# GhostFrame

A multi-frame variant impact scanner for cancer bioinformatics. GhostFrame re-examines "Silent" somatic mutations across all 6 reading frames to identify hidden non-synonymous effects in overlapping open reading frames (ORFs).

## What it does

A "Silent" mutation in standard cancer annotations means the canonical protein sequence is unchanged. But in regions where multiple ORFs overlap, the same nucleotide change may be missense or stop-gained in an alternative reading frame. GhostFrame scans all 6 frames, finds these hidden effects, and prioritizes the resulting mutant peptides as noncanonical neoantigen candidates.

**Output:** Interactive dashboard with Sankey reclassification flow, variant table, 3D frame explorer, and MHC binding scores. Also exports JSON/TSV for downstream use.

> **Research/educational use only. Not for clinical decision-making.**

## Quickstart

```bash
# Install uv if you don't have it
# https://docs.astral.sh/uv/getting-started/installation/

# Clone and setup
git clone <repo-url>
cd ghostframe
uv sync

# Run the ORF finder on the HPV16 demo
uv run --package ghostframe orfs data/demo/hpv16_k02718.fasta --min-len 50

# Fetch a sequence region from a local FASTA (seqfetch)
uv run --package ghostframe python -c "
from ghostframe.seqfetch import local
print(local.fetch('K02718.1', 0, 100, 'data/demo/hpv16_k02718.fasta'))
"

# Look up external evidence for a variant
uv run --package ghostframe python -c "
from ghostframe.models import NormalizedVariant
from ghostframe.evidence import clinvar, synmicdb
v = NormalizedVariant(chrom='17', pos=7675994, ref='G', alt='T', classification='Silent', gene='TP53')
print('SynMICdb:', synmicdb.lookup(v))
print('ClinVar:', clinvar.lookup(v))
"

# Run tests
uv run pytest

# Start the API server
uv run --package ghostframe-api uvicorn ghostframe_api.app:app --reload
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
        reclassify/       # Multi-frame reclassification (stubbed)
        peptides/         # Kmer generation (implemented)
        mhc/              # MHC binding prediction (implemented)
        evidence/         # External evidence linking (implemented)
        reports/          # Output generation (stubbed)
        pipeline/         # Orchestration (stubbed)
        cli/              # CLI entry points
    ghostframe-api/       # FastAPI server
  tests/                  # Test suite (mirrors source structure)
  data/demo/              # Sample data and expected outputs
  docs/                   # Architecture documentation
  frontend/               # Next.js frontend (placeholder)
```

## Pipeline architecture

GhostFrame uses a two-lane pipeline:

- **Fast Lane**: MAF intake -> filter Silent variants -> fetch reference sequence -> 6-frame ORF scan -> reclassify -> summary
- **Deep Lane**: Generate mutant peptides -> MHC binding prediction -> external evidence linking -> report

See [docs/architecture.md](docs/architecture.md) for details.

## Development

```bash
uv run pytest                    # run all tests
uv run pytest tests/orfs/        # run just ORF tests
uv run pytest -m golden          # run golden output tests
uv run ruff check .              # lint
uv run ruff format .             # format
uv run mypy packages/ghostframe/src/ghostframe/orfs/  # type check
```

## Team

UMGC BIFS617 group project.

## License

MIT
