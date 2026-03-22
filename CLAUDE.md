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
uv run pyright

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
| `httpx` | `seqfetch/remote.py`, `evidence/`, `domain/` | HTTP to Ensembl/NCBI/OpenProt/EMBL-EBI REST APIs |
| `pandas` | `variants/`, `evidence/synmicdb.py` | Tabular data manipulation |
| `mhcflurry` | `mhc/mhcflurry.py` | MHC-I binding prediction |
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
- **Branch naming**: `feat/<issue-number>-<short-slug>` (e.g. `feat/23-domain-annotation`)
- **No `__init__.py` in `tests/` subdirectories** — `--import-mode=importlib` makes them unnecessary; no other test subdirectory has one
- **Update docs after every change** — `README.md` (project layout, quickstart examples) and `docs/architecture.md` (module map status, remote API table) must stay current
- **API spike before implementing any external service** — test the actual endpoint with curl before writing any module code; verify URL, request format, response format, and rate limits empirically (issue specs and API docs are often stale or wrong)
- **Don't create stub files for deferred work** unless the issue explicitly requires them; a file that just raises `NotImplementedError` and has no planned implementation adds noise

## Module layout

| Module | Status | Purpose |
|--------|--------|---------|
| `orfs/` | Implemented | 6-frame ORF scanning (professor-gradable) |
| `variants/` | Implemented | MAF/VCF parsing and filtering |
| `seqfetch/` | Implemented | Reference sequence retrieval |
| `reclassify/` | Stubbed | Multi-frame reclassification engine |
| `peptides/` | Implemented | Kmer generation for MHC binding |
| `mhc/` | Implemented | MHC binding prediction (MHCflurry) |
| `domain/` | Implemented | Pfam domain annotation via EMBL-EBI HMMER JDispatcher |
| `evidence/` | Implemented | OpenProt, SynMICdb, ClinVar linking |
| `ranking/` | Implemented | Candidate scoring (scorer.py) and ranking (ranker.py + TSV export) |
| `reports/` | Partial | TSV export via ranking.ranker; JSON stubbed |
| `pipeline/` | Stubbed | Fast/deep lane orchestration |
| `cli/` | Partial | Click CLI entry points |
