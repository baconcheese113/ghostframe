# GhostFrame

A multi-frame variant impact scanner for cancer bioinformatics. GhostFrame re-examines "Silent" somatic mutations across all 6 reading frames to identify hidden non-synonymous effects in overlapping open reading frames (ORFs).

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
        variants/         # MAF/VCF intake (stubbed)
        seqfetch/         # Reference sequence retrieval (implemented)
        reclassify/       # Multi-frame reclassification (implemented)
        peptides/         # Kmer generation (stubbed)
        mhc/              # MHC binding prediction (stubbed)
        evidence/         # External evidence linking (stubbed)
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
