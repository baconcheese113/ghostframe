"""Tests for DNA sequence utilities — reverse complement, codon table, translation."""

import pytest

from ghostframe.orfs.sequence import CODON_TABLE, STOP_CODONS, reverse_complement, translate


class TestReverseComplement:
    """Tests for reverse_complement()."""

    def test_base_pairing(self) -> None:
        assert reverse_complement("A") == "T"
        assert reverse_complement("T") == "A"
        assert reverse_complement("C") == "G"
        assert reverse_complement("G") == "C"

    def test_reversal(self) -> None:
        assert reverse_complement("ATGC") == "GCAT"

    def test_mixed_case_normalized(self) -> None:
        assert reverse_complement("atgc") == "GCAT"
        assert reverse_complement("AtGc") == "GCAT"

    def test_palindrome(self) -> None:
        assert reverse_complement("AATT") == "AATT"

    def test_longer_sequence(self) -> None:
        seq = "ATGAAAGGATTTCCCGGG"
        rc = reverse_complement(seq)
        assert reverse_complement(rc) == seq


class TestTranslate:
    """Tests for translate()."""

    def test_start_codon(self) -> None:
        assert translate("ATG") == "M"

    def test_stop_codons(self) -> None:
        assert translate("TAA") == "*"
        assert translate("TAG") == "*"
        assert translate("TGA") == "*"

    def test_known_codons(self) -> None:
        assert translate("TTT") == "F"
        assert translate("GGG") == "G"
        assert translate("AAA") == "K"

    def test_full_orf(self) -> None:
        # ATG AAA GGA TTT CCC GGG TTT AAA CCC TGA
        # M   K   G   F   P   G   F   K   P   *
        protein = translate("ATGAAAGGATTTCCCGGGTTTAAACCCTGA")
        assert protein == "MKGFPGFKP*"

    def test_all_standard_codons_present(self) -> None:
        assert len(CODON_TABLE) == 64
        for codon, aa in CODON_TABLE.items():
            assert len(codon) == 3
            assert len(aa) == 1
            assert translate(codon) == aa

    def test_stop_codons_set(self) -> None:
        assert {"TAA", "TAG", "TGA"} == STOP_CODONS

    def test_length_not_multiple_of_3_raises(self) -> None:
        with pytest.raises(ValueError, match="not a multiple of 3"):
            translate("ATGC")

    def test_lowercase_input_normalized(self) -> None:
        assert translate("atg") == "M"
        assert translate("taa") == "*"

    def test_unknown_codon_returns_x(self) -> None:
        assert translate("NNN") == "X"
