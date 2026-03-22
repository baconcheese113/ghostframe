"""Tests for peptide kmer generation."""

from ghostframe.models import Peptide
from ghostframe.peptides.generator import sliding_kmers


class TestSlidingKmers:
    def test_windows_span_mut_pos(self) -> None:
        protein = "ACDEFGHIKLMNPQRSTVWY"  # 20 AA
        mut_pos = 10
        peptides = sliding_kmers(protein, mut_pos)
        for p in peptides:
            assert p.start <= mut_pos < p.start + p.k

    def test_all_k_lengths(self) -> None:
        protein = "ACDEFGHIKLMNPQRSTVWY"  # 20 AA
        peptides = sliding_kmers(protein, mut_pos=10)
        lengths = {p.k for p in peptides}
        assert lengths == {8, 9, 10, 11}

    def test_count_mid_protein(self) -> None:
        # 20 AA, mut_pos=10, k=8: start ranges from max(0,3)=3 to min(12,10)=10 → 8 windows
        protein = "ACDEFGHIKLMNPQRSTVWY"
        peptides = sliding_kmers(protein, mut_pos=10, k_min=8, k_max=8)
        assert len(peptides) == 8

    def test_mut_pos_at_start(self) -> None:
        protein = "ACDEFGHIKLMNPQRSTVWY"
        peptides = sliding_kmers(protein, mut_pos=0, k_min=8, k_max=8)
        # Only start=0 is valid
        assert len(peptides) == 1
        assert peptides[0].start == 0

    def test_mut_pos_at_end(self) -> None:
        protein = "ACDEFGHIKLMNPQRSTVWY"  # len=20, last pos=19
        peptides = sliding_kmers(protein, mut_pos=19, k_min=8, k_max=8)
        # Only start=12 is valid (12 + 8 = 20)
        assert len(peptides) == 1
        assert peptides[0].start == 12

    def test_skip_stop_codon(self) -> None:
        # Place '*' inside the mutation window
        protein = "ACDEFGHIK*MNPQRSTVWY"  # '*' at pos 9
        peptides = sliding_kmers(protein, mut_pos=9, k_min=8, k_max=8)
        assert all("*" not in p.sequence for p in peptides)

    def test_skip_unknown_aa(self) -> None:
        protein = "ACDEFGHIKXMNPQRSTVWY"  # 'X' at pos 9
        peptides = sliding_kmers(protein, mut_pos=9, k_min=8, k_max=8)
        assert all("X" not in p.sequence for p in peptides)

    def test_protein_shorter_than_k_min(self) -> None:
        protein = "ACDE"  # len=4, k_min=8
        peptides = sliding_kmers(protein, mut_pos=2)
        assert peptides == []

    def test_peptide_fields(self) -> None:
        protein = "ACDEFGHIKLMNPQRSTVWY"
        peptides = sliding_kmers(protein, mut_pos=5, k_min=8, k_max=8)
        for p in peptides:
            assert isinstance(p, Peptide)
            assert len(p.sequence) == p.k == 8
            assert p.sequence == protein[p.start : p.start + p.k]

    def test_custom_k_range(self) -> None:
        protein = "ACDEFGHIKLMNPQRSTVWY"
        peptides = sliding_kmers(protein, mut_pos=10, k_min=9, k_max=9)
        assert all(p.k == 9 for p in peptides)
        assert all(len(p.sequence) == 9 for p in peptides)
