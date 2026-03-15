"""Shared test fixtures for GhostFrame tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def simple_fasta_path() -> Path:
    """Path to simple.fasta test fixture."""
    return FIXTURES_DIR / "simple.fasta"


@pytest.fixture
def multi_seq_fasta_path() -> Path:
    """Path to multi_seq.fasta test fixture."""
    return FIXTURES_DIR / "multi_seq.fasta"


@pytest.fixture
def edge_cases_fasta_path() -> Path:
    """Path to edge_cases.fasta test fixture."""
    return FIXTURES_DIR / "edge_cases.fasta"


@pytest.fixture
def sample_maf_path() -> Path:
    """Path to sample.maf test fixture."""
    return FIXTURES_DIR / "sample.maf"
