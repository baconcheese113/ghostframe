"""Tests for seqfetch: local fetch, remote fetch, and window extraction."""

from pathlib import Path

import pytest

from ghostframe.models import NormalizedVariant
from ghostframe.seqfetch import local, window


class TestLocalFetch:
    def test_full_sequence(self, tmp_path: Path) -> None:
        fasta = tmp_path / "test.fasta"
        fasta.write_text(">chr1\nATGCATGCATGC\n", encoding="utf-8")
        result = local.fetch("chr1", 0, 12, fasta)
        assert result == "ATGCATGCATGC"

    def test_slice(self, tmp_path: Path) -> None:
        fasta = tmp_path / "test.fasta"
        fasta.write_text(">chr1\nATGCATGCATGC\n", encoding="utf-8")
        result = local.fetch("chr1", 4, 8, fasta)
        assert result == "ATGC"

    def test_returns_uppercase(self, tmp_path: Path) -> None:
        fasta = tmp_path / "test.fasta"
        fasta.write_text(">chr1\natgcatgc\n", encoding="utf-8")
        result = local.fetch("chr1", 0, 4, fasta)
        assert result == "ATGC"

    def test_multi_line_sequence(self, tmp_path: Path) -> None:
        fasta = tmp_path / "test.fasta"
        fasta.write_text(">chr1\nATGCAT\nGCATGC\n", encoding="utf-8")
        result = local.fetch("chr1", 0, 12, fasta)
        assert result == "ATGCATGCATGC"


class TestWindowExtract:
    def _make_variant(self, chrom: str = "chr1", pos: int = 10) -> NormalizedVariant:
        return NormalizedVariant(
            chrom=chrom, pos=pos, ref="A", alt="T",
            classification="Silent", gene="TP53",
        )

    def test_window_chrom_and_bounds(self) -> None:
        seq = "A" * 1000
        v = self._make_variant(pos=501)
        gw = window.extract(v, seq, flank=10)
        assert gw.chrom == "chr1"
        assert gw.start == 490   # 0-based: pos-1-flank = 500-10
        assert gw.end == 511     # pos-1+len(ref)+flank = 500+1+10
        assert len(gw.sequence) == 21

    def test_window_clamps_at_zero(self) -> None:
        seq = "A" * 100
        v = self._make_variant(pos=1)
        gw = window.extract(v, seq, flank=50)
        assert gw.start == 0

    def test_window_sequence_is_uppercase(self) -> None:
        seq = "atgc" * 100
        v = self._make_variant(pos=50)
        gw = window.extract(v, seq, flank=5)
        assert gw.sequence == gw.sequence.upper()

    def test_window_correct_slice(self) -> None:
        # variant at pos=11 (1-based) → 0-based idx 10, flank=2
        # start=8, end=13 → seq[8:13]
        seq = "AAAAAAAATTTTTGGGGG"
        v = self._make_variant(pos=11)
        gw = window.extract(v, seq, flank=2)
        assert gw.start == 8
        assert gw.end == 13
        assert gw.sequence == "TTTTT"


@pytest.mark.slow
@pytest.mark.integration
class TestRemoteFetch:
    def test_returns_dna_string(self) -> None:
        from ghostframe.seqfetch import remote
        seq = remote.fetch("1", 1000000, 1000010)
        assert set(seq).issubset(set("ATGCN"))
        assert len(seq) == 11

    def test_returns_uppercase(self) -> None:
        from ghostframe.seqfetch import remote
        seq = remote.fetch("1", 1000000, 1000005)
        assert seq == seq.upper()
