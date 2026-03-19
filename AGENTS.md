# GhostFrame — AI Agent Conventions

See CLAUDE.md for full project conventions. This file provides the same guidance for OpenAI Codex and other AI coding agents.

## Quick reference

- **Language**: Python >= 3.13
- **Package manager**: uv (workspace monorepo)
- **Core library**: `packages/ghostframe/` — dataclasses, Click CLI
- **API**: `packages/ghostframe-api/` — FastAPI, Pydantic
- **Tests**: `uv run pytest` (use `--import-mode=importlib`)
- **Lint**: `uv run ruff check .`
- **Format**: `uv run ruff check --select I --fix && uv run ruff format`
- **Type check**: `uv run mypy packages/ghostframe/src/ghostframe/orfs/`

## Third-party libraries

Always search for well-maintained open source libraries before writing new logic. Prefer a library if it meaningfully reduces complexity — don't reinvent wheels. Key deps in use:

- `pyfaidx` — indexed FASTA access (`seqfetch/local.py`)
- `httpx` — async HTTP to Ensembl/UCSC REST (`seqfetch/remote.py`)
- `pandas` — tabular data manipulation (`reports/`, `variants/`)

When planning or implementing any module, ask: *is there a standard library or well-known package that already does this?*

## Important

- Use `uv run --package ghostframe` or `uv run --package ghostframe-api` for CLI/API commands
- Stubbed modules raise `NotImplementedError` — don't remove these, implement them
- Golden tests compare exact string output — don't change formatting without updating expected outputs
- No `from __future__ import annotations` — Python 3.13 supports native union syntax
