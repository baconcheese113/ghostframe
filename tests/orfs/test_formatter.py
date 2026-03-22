"""Tests for ORF output formatting."""

from pathlib import Path

import pytest

from ghostframe.models import ORF, FastaRecord
from ghostframe.orfs.formatter import CODONS_PER_LINE, format_all_orfs, format_orf


@pytest.fixture
def record() -> FastaRecord:
    return FastaRecord(
        id="test_seq",
        description="test_seq A test sequence",
        sequence="ATGAAAGGATTTCCCGGGTTTAAACCCTGA",
    )


class TestFormatOrf:
    """Tests for format_orf()."""

    def test_header_format(self, record: FastaRecord) -> None:
        orf = ORF(frame=1, pos=1, length=30, dna="ATGAAAGGATTTCCCGGGTTTAAACCCTGA")
        output = format_orf(record, orf)
        lines = output.split("\n")
        assert lines[0] == ">test_seq A test sequence | FRAME = 1 POS = 1 LEN = 30"

    def test_codon_spacing(self, record: FastaRecord) -> None:
        orf = ORF(frame=1, pos=1, length=30, dna="ATGAAAGGATTTCCCGGGTTTAAACCCTGA")
        output = format_orf(record, orf)
        lines = output.split("\n")
        # Second line has codons separated by spaces
        codons = lines[1].split(" ")
        assert all(len(c) == 3 for c in codons)

    def test_15_codons_per_line(self, record: FastaRecord) -> None:
        # Create a long ORF: 48 codons = 144 bases
        dna = "ATG" + "AAA" * 46 + "TGA"
        orf = ORF(frame=1, pos=1, length=len(dna), dna=dna)
        output = format_orf(record, orf)
        lines = output.split("\n")
        # First data line (lines[1]) should have exactly 15 codons
        codons_line1 = lines[1].split(" ")
        assert len(codons_line1) == CODONS_PER_LINE

    def test_last_line_partial(self, record: FastaRecord) -> None:
        # 10 codons = 30 bases → single line, less than 15
        orf = ORF(frame=1, pos=1, length=30, dna="ATGAAAGGATTTCCCGGGTTTAAACCCTGA")
        output = format_orf(record, orf)
        lines = output.split("\n")
        codons_last = lines[-1].split(" ")
        assert len(codons_last) == 10
        assert len(codons_last) < CODONS_PER_LINE

    def test_single_codon_pair_orf(self, record: FastaRecord) -> None:
        # ATG TAA = 2 codons
        orf = ORF(frame=1, pos=1, length=6, dna="ATGTAA")
        output = format_orf(record, orf)
        lines = output.split("\n")
        assert len(lines) == 2  # header + 1 data line
        assert lines[1] == "ATG TAA"

    def test_negative_position_reverse_frame(self, record: FastaRecord) -> None:
        orf = ORF(frame=4, pos=-1, length=9, dna="ATGAAATGA")
        output = format_orf(record, orf)
        assert "FRAME = 4 POS = -1 LEN = 9" in output

    def test_exact_15_codons_one_line(self, record: FastaRecord) -> None:
        # Exactly 15 codons = 45 bases → one full data line
        dna = "ATG" + "AAA" * 13 + "TGA"
        orf = ORF(frame=1, pos=1, length=len(dna), dna=dna)
        output = format_orf(record, orf)
        lines = output.split("\n")
        assert len(lines) == 2  # header + 1 line of exactly 15 codons
        assert len(lines[1].split(" ")) == 15


class TestFormatAllOrfs:
    """Tests for format_all_orfs()."""

    def test_empty_orfs(self, record: FastaRecord) -> None:
        output = format_all_orfs(record, [])
        assert output == ""

    def test_multiple_orfs(self, record: FastaRecord) -> None:
        orfs = [
            ORF(frame=1, pos=1, length=9, dna="ATGAAATGA"),
            ORF(frame=2, pos=2, length=9, dna="ATGCCCTGA"),
        ]
        output = format_all_orfs(record, orfs)
        assert output.count("FRAME = ") == 2


@pytest.mark.golden
class TestGoldenOutput:
    """Golden output tests — compare exact strings."""

    def test_simple_fasta_output(self, simple_fasta_path: Path) -> None:
        from ghostframe.orfs.fasta import parse_file
        from ghostframe.orfs.scanner import find_orfs

        records = parse_file(simple_fasta_path)
        record = records[0]
        orfs = find_orfs(record.sequence, min_length=6)

        output = format_all_orfs(record, orfs)
        # Frame 1 ORF should be present
        assert "FRAME = 1 POS = 1 LEN = 30" in output
        # Verify codon-spaced output
        assert "ATG AAA GGA TTT CCC GGG TTT AAA CCC TGA" in output

    def test_multi_seq_output(self, multi_seq_fasta_path: Path) -> None:
        from ghostframe.orfs.fasta import parse_file
        from ghostframe.orfs.scanner import find_orfs

        records = parse_file(multi_seq_fasta_path)
        all_output_parts: list[str] = []
        for record in records:
            orfs = find_orfs(record.sequence, min_length=6)
            part = format_all_orfs(record, orfs)
            if part:
                all_output_parts.append(part)

        full_output = "\n".join(all_output_parts)
        # seq1 should have its ORF
        assert "seq1 First sequence" in full_output
        assert "FRAME = 1" in full_output
