"""Tests for FASTA parsing — covers both parse_file and parse_text."""

from pathlib import Path

from ghostframe.orfs.fasta import parse_file, parse_text


class TestParseFile:
    """Tests for parse_file()."""

    def test_parse_single_sequence(self, simple_fasta_path: Path) -> None:
        records = parse_file(simple_fasta_path)
        assert len(records) == 1
        assert records[0].id == "simple_test"
        assert "simple test sequence" in records[0].description.lower()

    def test_parse_multi_sequence(self, multi_seq_fasta_path: Path) -> None:
        records = parse_file(multi_seq_fasta_path)
        assert len(records) == 3
        assert records[0].id == "seq1"
        assert records[1].id == "seq2"
        assert records[2].id == "seq3"


class TestParseText:
    """Tests for parse_text()."""

    def test_single_sequence(self) -> None:
        text = ">test\nATGCATGC\n"
        records = parse_text(text)
        assert len(records) == 1
        assert records[0].sequence == "ATGCATGC"

    def test_multi_sequence(self) -> None:
        text = ">seq1\nATGC\n>seq2\nGCTA\n>seq3\nTTTT\n"
        records = parse_text(text)
        assert len(records) == 3

    def test_sequences_split_across_lines(self) -> None:
        text = ">test\nATGC\nATGC\nATGC\n"
        records = parse_text(text)
        assert records[0].sequence == "ATGCATGCATGC"

    def test_ignore_whitespace_in_sequence(self) -> None:
        text = ">test\nATG C AT GC\n"
        records = parse_text(text)
        assert records[0].sequence == "ATGCATGC"

    def test_normalize_mixed_case(self) -> None:
        text = ">test\natgcATGC\n"
        records = parse_text(text)
        assert records[0].sequence == "ATGCATGC"

    def test_preserve_full_header(self) -> None:
        text = ">gi|12345| Some organism description\nATGC\n"
        records = parse_text(text)
        assert records[0].description == "gi|12345| Some organism description"
        assert records[0].id == "gi|12345|"

    def test_handle_empty_lines_between_sequences(self) -> None:
        text = ">seq1\nATGC\n\n>seq2\nGCTA\n"
        records = parse_text(text)
        assert len(records) == 2

    def test_handle_trailing_newlines(self) -> None:
        text = ">test\nATGC\n\n\n"
        records = parse_text(text)
        assert len(records) == 1
        assert records[0].sequence == "ATGC"

    def test_empty_text_returns_empty(self) -> None:
        records = parse_text("")
        assert records == []

    def test_no_headers_returns_empty(self) -> None:
        records = parse_text("ATGCATGC\nGCTAGCTA\n")
        assert records == []
