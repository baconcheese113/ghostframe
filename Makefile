.PHONY: setup fmt lint typecheck test test-golden test-cov orfs dev-api clean

setup:
	uv sync --all-packages
	uv run pre-commit install

fmt:
	uv run ruff check --select I --fix .
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run pyright

test:
	uv run pytest

test-golden:
	uv run pytest -m golden

test-cov:
	uv run pytest --cov=ghostframe --cov-report=term-missing

orfs:
	uv run --package ghostframe orfs $(ARGS)

dev-api:
	uv run --package ghostframe-api uvicorn ghostframe_api.app:app --reload --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pyright -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache .coverage htmlcov
