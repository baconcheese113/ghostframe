# GhostFrame — Claude Code Conventions

## Project overview

GhostFrame is a multi-frame variant impact scanner for cancer bioinformatics. It re-examines "Silent" mutations across all 6 reading frames to find hidden non-synonymous effects in overlapping ORFs.

## Repository structure

- **uv workspace monorepo** with two members:
  - `packages/ghostframe/` — core Python library (Click CLI, no Pydantic)
  - `packages/ghostframe-api/` — FastAPI server (Pydantic at boundary)
- `tests/` — mirrors source structure, run subsets via `pytest tests/orfs/`
- `data/demo/` — sample FASTA files and expected outputs
- `frontend/` — Next.js (placeholder only)

## Key commands

```bash
# Setup
uv sync

# Run tests
uv run pytest                         # all tests
uv run pytest tests/orfs/             # just ORF tests
uv run pytest -m golden               # golden output tests

# Lint and format
uv run ruff check .                   # lint
uv run ruff check --select I --fix && uv run ruff format   # format

# Type check
uv run mypy packages/ghostframe/src/ghostframe/orfs/

# Run CLI
uv run --package ghostframe orfs data/demo/hpv16_k02718.fasta --min-len 50

# Run API
uv run --package ghostframe-api uvicorn ghostframe_api.app:app --reload
```

## Third-party libraries

Always search for well-maintained open source libraries before writing new logic. Prefer a library if it meaningfully reduces complexity — don't reinvent wheels. Key deps in use:

| Library | Used in | Purpose |
|---|---|---|
| `click` | `cli/` | CLI framework |
| `pyfaidx` | `seqfetch/local.py` | Indexed FASTA access |
| `httpx` | `seqfetch/remote.py` | Async HTTP to Ensembl/UCSC REST |
| `pandas` | `reports/`, `variants/` | Tabular data manipulation |
| `fastapi` + `pydantic` | `ghostframe-api` | API boundary only |

When planning or implementing any module, ask: *is there a standard library or well-known package that already does this?*

## Conventions

- **Python >= 3.13** — use native `X | Y` union syntax, no `from __future__ import annotations`
- **dataclasses** in core library, **Pydantic** only in `ghostframe-api`
- **Type hints** on all function signatures
- **`--import-mode=importlib`** for pytest (configured in root pyproject.toml)
- **`--package` flag** required for `uv run` when targeting workspace members
- Golden test fixtures in `tests/fixtures/`, expected outputs in `data/demo/`
- Stubbed modules use `raise NotImplementedError("...")` with typed signatures
- Test markers: `@pytest.mark.golden`, `@pytest.mark.integration`, `@pytest.mark.slow`

## Module layout

| Module | Status | Purpose |
|--------|--------|---------|
| `orfs/` | Implemented | 6-frame ORF scanning (professor-gradable) |
| `variants/` | Stubbed | MAF/VCF parsing and filtering |
| `seqfetch/` | Stubbed | Reference sequence retrieval |
| `reclassify/` | Stubbed | Multi-frame reclassification engine |
| `peptides/` | Stubbed | Kmer generation for MHC binding |
| `mhc/` | Stubbed | MHC binding prediction |
| `evidence/` | Stubbed | External database linking |
| `reports/` | Stubbed | Output generation |
| `pipeline/` | Stubbed | Fast/deep lane orchestration |
| `cli/` | Partial | Click CLI entry points |
