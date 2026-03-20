"""Tests for the fast lane pipeline orchestrator."""

from pathlib import Path

import pytest

from ghostframe.models import FastLaneResult, ReclassifySummary
from ghostframe.pipeline import fast_lane

DEMO_MAF = Path("data/demo/sample.maf")
DEMO_FASTA = Path("data/demo/hpv16_k02718.fasta")


class TestFastLaneRun:
    def test_requires_fasta_path(self) -> None:
        with pytest.raises(ValueError, match="fasta_path is required"):
            fast_lane.run(DEMO_MAF, fasta_path=None)

    @pytest.mark.integration
    def test_returns_fast_lane_result(self) -> None:
        result = fast_lane.run(DEMO_MAF, DEMO_FASTA)
        assert isinstance(result, FastLaneResult)
        assert isinstance(result.summary, ReclassifySummary)
        assert isinstance(result.reclassified_variants, list)
        assert isinstance(result.sankey_data, list)

    @pytest.mark.integration
    def test_sankey_data_matches_summary(self) -> None:
        result = fast_lane.run(DEMO_MAF, DEMO_FASTA)
        assert result.sankey_data is result.summary.sankey_data

    @pytest.mark.integration
    def test_min_len_filters_orfs(self) -> None:
        result_short = fast_lane.run(DEMO_MAF, DEMO_FASTA, min_len=1)
        result_long = fast_lane.run(DEMO_MAF, DEMO_FASTA, min_len=10000)
        # A very large min_len should yield fewer (or equal) effects
        assert len(result_long.reclassified_variants) <= len(result_short.reclassified_variants)
