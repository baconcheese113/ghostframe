"""Tests for 6-frame ORF scanning engine."""

import pytest

from ghostframe.orfs.scanner import find_orfs, find_orfs_in_frame


class TestFindOrfsInFrame:
    """Tests for find_orfs_in_frame() — single frame scanning."""

    def test_happy_path_frame_1(self) -> None:
        # ATG AAA GGA TTT CCC GGG TTT AAA CCC TGA = 30 bases
        seq = "ATGAAAGGATTTCCCGGGTTTAAACCCTGA"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert len(orfs) == 1
        assert orfs[0].frame == 1
        assert orfs[0].pos == 1
        assert orfs[0].length == 30
        assert orfs[0].dna == seq

    def test_frame_2(self) -> None:
        # offset 1: skip first base, then read triplets
        # _ATG AAA TGA ...
        seq = "XATGAAATGA"
        orfs = find_orfs_in_frame(seq, frame=2, min_length=6)
        assert len(orfs) == 1
        assert orfs[0].frame == 2
        assert orfs[0].pos == 2  # 1-based from offset 1
        assert orfs[0].dna == "ATGAAATGA"

    def test_frame_3(self) -> None:
        # offset 2: skip first two bases
        seq = "XXATGAAATGA"
        orfs = find_orfs_in_frame(seq, frame=3, min_length=6)
        assert len(orfs) == 1
        assert orfs[0].frame == 3
        assert orfs[0].pos == 3

    def test_maximal_orf_uses_first_atg(self) -> None:
        # ATG AAG ATG CCC GGA TGA
        # Two ATGs before one stop → maximal ORF from first ATG
        seq = "ATGAAGATGCCCGGATGA"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert len(orfs) == 1
        assert orfs[0].dna == seq
        assert orfs[0].length == 18

    def test_multiple_non_overlapping_orfs(self) -> None:
        # Two ORFs separated by a stop
        seq = "ATGAAATGAATGCCCTGA"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert len(orfs) == 2
        assert orfs[0].dna == "ATGAAATGA"
        assert orfs[1].dna == "ATGCCCTGA"

    def test_min_length_excludes_short(self) -> None:
        seq = "ATGAAATGA"  # 9 bases
        orfs = find_orfs_in_frame(seq, frame=1, min_length=12)
        assert len(orfs) == 0

    def test_min_length_includes_exact(self) -> None:
        seq = "ATGAAATGA"  # 9 bases
        orfs = find_orfs_in_frame(seq, frame=1, min_length=9)
        assert len(orfs) == 1

    def test_stop_codon_included_in_orf(self) -> None:
        seq = "ATGAAATGA"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert orfs[0].dna.endswith("TGA")
        assert orfs[0].length == 9

    def test_no_atg_returns_empty(self) -> None:
        seq = "TTTCCCGGGTTTAAACCCTGA"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert orfs == []

    def test_atg_immediately_followed_by_stop(self) -> None:
        seq = "ATGTAA"  # 6 bases
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert len(orfs) == 1
        assert orfs[0].length == 6

    def test_no_stop_codon_no_orf(self) -> None:
        # ATG followed by sequence end — not maximal, no ORF reported
        seq = "ATGAAAGGATTTCCCGGG"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert orfs == []

    def test_orf_at_first_nucleotide(self) -> None:
        seq = "ATGAAATGA"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=6)
        assert orfs[0].pos == 1

    def test_all_stop_sequence(self) -> None:
        seq = "TAATAGTGA"
        orfs = find_orfs_in_frame(seq, frame=1, min_length=3)
        assert orfs == []


class TestFindOrfsReverseFrames:
    """Tests for reverse complement frames (4-6)."""

    def test_reverse_frame_position_negative(self) -> None:
        # Frame 4 = reverse complement, offset 0
        seq = "ATGAAATGA"
        orfs = find_orfs_in_frame(seq, frame=4, min_length=6, original_seq_len=9)
        for orf in orfs:
            assert orf.pos < 0

    def test_reverse_frame_4(self) -> None:
        # Reverse complement of seq that has ATG...stop in rc
        # TCATTTCAT -> reverse complement is ATGAAATGA
        from ghostframe.orfs.sequence import reverse_complement

        seq = "TCATTTCAT"
        rc = reverse_complement(seq)
        assert rc == "ATGAAATGA"
        orfs = find_orfs_in_frame(rc, frame=4, min_length=6, original_seq_len=len(seq))
        assert len(orfs) == 1
        assert orfs[0].frame == 4
        assert orfs[0].pos == -1


class TestFindOrfs:
    """Tests for find_orfs() — all 6 frames."""

    def test_default_min_length_is_50(self) -> None:
        # Short sequence: ORF is 30 bases, should be excluded by default min_length=50
        seq = "ATGAAAGGATTTCCCGGGTTTAAACCCTGA"
        orfs = find_orfs(seq)
        assert orfs == []

    def test_custom_min_length(self) -> None:
        seq = "ATGAAAGGATTTCCCGGGTTTAAACCCTGA"
        orfs = find_orfs(seq, min_length=6)
        assert len(orfs) >= 1

    def test_orfs_ordered_by_frame(self) -> None:
        # A longer sequence that might have ORFs in multiple frames
        seq = "ATGAAAGGATTTCCCGGGTTTAAACCCTGA"
        orfs = find_orfs(seq, min_length=6)
        frames = [orf.frame for orf in orfs]
        assert frames == sorted(frames)

    @pytest.mark.golden
    def test_simple_fasta_sequence(self, simple_fasta_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.orfs.fasta import parse_file

        records = parse_file(simple_fasta_path)
        assert len(records) == 1
        orfs = find_orfs(records[0].sequence, min_length=6)
        # Should find at least the known frame-1 ORF
        frame1_orfs = [o for o in orfs if o.frame == 1]
        assert len(frame1_orfs) >= 1
        assert frame1_orfs[0].dna == "ATGAAAGGATTTCCCGGGTTTAAACCCTGA"

    @pytest.mark.golden
    def test_multi_seq(self, multi_seq_fasta_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.orfs.fasta import parse_file

        records = parse_file(multi_seq_fasta_path)
        assert len(records) == 3
        # seq2 has only a 12-base ORF (ATGTAATTTGGG has ATG TAA at pos 0 = 6 bases)
        orfs_seq2 = find_orfs(records[1].sequence, min_length=6)
        frame1_seq2 = [o for o in orfs_seq2 if o.frame == 1]
        assert len(frame1_seq2) >= 1
        assert frame1_seq2[0].length == 6  # ATG TAA

    def test_edge_case_no_atg(self, edge_cases_fasta_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.orfs.fasta import parse_file

        records = parse_file(edge_cases_fasta_path)
        no_atg = next(r for r in records if r.id == "edge_no_atg")
        orfs = find_orfs(no_atg.sequence, min_length=6)
        frame1_orfs = [o for o in orfs if o.frame == 1]
        assert frame1_orfs == []

    def test_edge_case_atg_stop(self, edge_cases_fasta_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.orfs.fasta import parse_file

        records = parse_file(edge_cases_fasta_path)
        atg_stop = next(r for r in records if r.id == "edge_atg_stop")
        orfs = find_orfs(atg_stop.sequence, min_length=6)
        frame1_orfs = [o for o in orfs if o.frame == 1]
        assert len(frame1_orfs) == 1
        assert frame1_orfs[0].length == 6

    def test_edge_case_no_stop(self, edge_cases_fasta_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.orfs.fasta import parse_file

        records = parse_file(edge_cases_fasta_path)
        no_stop = next(r for r in records if r.id == "edge_no_stop")
        orfs = find_orfs(no_stop.sequence, min_length=6)
        frame1_orfs = [o for o in orfs if o.frame == 1]
        # No stop codon → not maximal → no ORF
        assert frame1_orfs == []

    def test_edge_case_overlapping_atg(self, edge_cases_fasta_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.orfs.fasta import parse_file

        records = parse_file(edge_cases_fasta_path)
        overlapping = next(r for r in records if r.id == "edge_overlapping_atg")
        orfs = find_orfs(overlapping.sequence, min_length=6)
        frame1_orfs = [o for o in orfs if o.frame == 1]
        assert len(frame1_orfs) == 1
        # Maximal: uses first ATG
        assert frame1_orfs[0].dna.startswith("ATG")
        assert frame1_orfs[0].pos == 1

    def test_edge_case_boundary_orf(self, edge_cases_fasta_path) -> None:  # type: ignore[no-untyped-def]
        from ghostframe.orfs.fasta import parse_file

        records = parse_file(edge_cases_fasta_path)
        boundary = next(r for r in records if r.id == "edge_boundary")
        orfs = find_orfs(boundary.sequence, min_length=6)
        frame1_orfs = [o for o in orfs if o.frame == 1]
        assert len(frame1_orfs) == 1
        assert frame1_orfs[0].pos == 1

    def test_codon_alignment(self) -> None:
        # Ensure the scanner reads in triplets from the frame offset
        # Frame 2 offset 1: skip first base, then triplets
        seq = "XATGAAATGA"
        orfs = find_orfs(seq, min_length=6)
        frame2 = [o for o in orfs if o.frame == 2]
        assert len(frame2) == 1
        assert frame2[0].dna == "ATGAAATGA"
