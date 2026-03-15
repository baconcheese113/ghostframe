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

## Important

- Use `uv run --package ghostframe` or `uv run --package ghostframe-api` for CLI/API commands
- Stubbed modules raise `NotImplementedError` — don't remove these, implement them
- Golden tests compare exact string output — don't change formatting without updating expected outputs
- No `from __future__ import annotations` — Python 3.13 supports native union syntax
