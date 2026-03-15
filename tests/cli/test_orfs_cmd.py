"""Tests for the ORF CLI command."""

from pathlib import Path

from click.testing import CliRunner

from ghostframe.cli.orfs import main


class TestOrfsCli:
    """Tests for the `orfs` CLI command."""

    def test_help_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Find all open reading frames" in result.output

    def test_simple_fasta(self, simple_fasta_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [str(simple_fasta_path), "--min-len", "6"])
        assert result.exit_code == 0
        assert "FRAME = 1 POS = 1 LEN = 30" in result.output
        assert "ATG AAA GGA TTT CCC GGG TTT AAA CCC TGA" in result.output

    def test_default_min_length(self, simple_fasta_path: Path) -> None:
        runner = CliRunner()
        # simple.fasta ORF is 30 bases, default min_length=50 → should find nothing
        result = runner.invoke(main, [str(simple_fasta_path), "--min-len", "50"])
        assert result.exit_code == 0
        assert "FRAME" not in result.output

    def test_custom_min_length(self, multi_seq_fasta_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [str(multi_seq_fasta_path), "--min-len", "6"])
        assert result.exit_code == 0
        assert "FRAME" in result.output

    def test_missing_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["/nonexistent/file.fasta", "--min-len", "50"])
        assert result.exit_code != 0

    def test_empty_fasta(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.fasta"
        empty.write_text("")
        runner = CliRunner()
        result = runner.invoke(main, [str(empty), "--min-len", "6"])
        assert result.exit_code == 0
        assert result.output.strip() == ""
