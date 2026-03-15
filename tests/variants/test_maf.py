"""Tests for MAF parsing — stubbed/skipped until variants module is implemented."""

import pytest


@pytest.mark.skip(reason="variants.maf not yet implemented")
class TestMafParse:
    def test_parse_maf_file(self, sample_maf_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.variants.maf import parse

        variants = parse(sample_maf_path)
        assert len(variants) == 3

    def test_filter_silent(self) -> None:

        # Will be tested once implemented
        assert True
