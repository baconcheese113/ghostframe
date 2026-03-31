"""Tests for the reclassification engine, codon effect comparison, and summary."""

from ghostframe.models import ORF, FrameEffect, GenomicWindow, NormalizedVariant
from ghostframe.reclassify import codon_effect, engine, summary


def _variant(pos: int, alt: str, classification: str = "Silent") -> NormalizedVariant:
    return NormalizedVariant(
        chrom="chr1", pos=pos, ref="N", alt=alt, classification=classification, gene="TEST"
    )


def _window(sequence: str, start: int = 0) -> GenomicWindow:
    return GenomicWindow(chrom="chr1", start=start, end=start + len(sequence), sequence=sequence)


def _orf(frame: int, pos: int, dna: str) -> ORF:
    return ORF(frame=frame, pos=pos, length=len(dna), dna=dna)


class TestCodonEffect:
    def test_synonymous(self) -> None:
        result = codon_effect.compare("TTT", "TTC")
        assert result.ref_aa == "F"
        assert result.alt_aa == "F"
        assert result.effect_type == "synonymous"

    def test_missense(self) -> None:
        # GAA (E) → GCA (A): different amino acids, neither is stop or start
        result = codon_effect.compare("GAA", "GCA")
        assert result.ref_aa == "E"
        assert result.alt_aa == "A"
        assert result.effect_type == "missense"

    def test_stop_gain(self) -> None:
        result = codon_effect.compare("AAA", "TAA")
        assert result.ref_aa == "K"
        assert result.alt_aa == "*"
        assert result.effect_type == "stop_gain"

    def test_stop_loss(self) -> None:
        result = codon_effect.compare("TAA", "AAA")
        assert result.ref_aa == "*"
        assert result.alt_aa == "K"
        assert result.effect_type == "stop_loss"

    def test_start_loss(self) -> None:
        result = codon_effect.compare("ATG", "TTG")
        assert result.ref_aa == "M"
        assert result.alt_aa == "L"
        assert result.effect_type == "start_loss"

    def test_uppercase_normalization(self) -> None:
        # lowercase input: gaa (E) → gca (A) → missense
        result = codon_effect.compare("gaa", "gca")
        assert result.ref_aa == "E"
        assert result.alt_aa == "A"
        assert result.effect_type == "missense"


class TestReclassifyEngine:
    def test_forward_frame_missense(self) -> None:
        # Window: ATGACGTTT (pos 0-8), start=0
        # ORF: frame 1, pos=1, dna="ATGACGTTT" → ATG ACG TTT → M T F
        # Variant at pos=4 (window idx 3), alt="T"
        # Codon 1 (ACG): base_in_codon=0 → TCG → S  (M→T missense is codon 1)
        seq = "ATGACGTTT"
        orf = _orf(frame=1, pos=1, dna=seq)
        window = _window(seq)
        var = _variant(pos=4, alt="T", classification="Silent")

        effects = engine.reclassify(var, [orf], window)

        assert len(effects) == 1
        assert effects[0].new_class == "Missense"
        assert effects[0].ref_aa == "T"
        assert effects[0].alt_aa == "S"
        assert effects[0].old_class == "Silent"

    def test_forward_frame_synonymous(self) -> None:
        # Window: ATGACGTTT, variant at pos=9 (last base), alt="C"
        # Codon 2 (TTT, idx 6-8): base_in_codon=2 → TTC → F (synonymous)
        seq = "ATGACGTTT"
        orf = _orf(frame=1, pos=1, dna=seq)
        window = _window(seq)
        var = _variant(pos=9, alt="C", classification="Silent")

        effects = engine.reclassify(var, [orf], window)

        assert len(effects) == 1
        assert effects[0].new_class == "Silent"
        assert effects[0].ref_aa == "F"
        assert effects[0].alt_aa == "F"

    def test_nonzero_window_start(self) -> None:
        # Same scenario as test_forward_frame_missense but with window.start=100.
        # variant.pos=104 (absolute), orf.pos=1 (window-local), window.start=100.
        # variant_window_idx = 104 - 1 - 100 = 3; same offset as the zero-start case.
        seq = "ATGACGTTT"
        orf = _orf(frame=1, pos=1, dna=seq)
        window = GenomicWindow(chrom="chr1", start=100, end=109, sequence=seq)
        var = _variant(pos=104, alt="T", classification="Silent")

        effects = engine.reclassify(var, [orf], window)

        assert len(effects) == 1
        assert effects[0].new_class == "Missense"
        assert effects[0].ref_aa == "T"
        assert effects[0].alt_aa == "S"

    def test_variant_not_in_orf(self) -> None:
        # ORF spans positions 1-9 (length 9); variant at pos=20 is outside
        seq = "ATGACGTTT"
        orf = _orf(frame=1, pos=1, dna=seq)
        window = _window("ATGACGTTTNNNNNNNNNNNN")
        var = _variant(pos=20, alt="T", classification="Silent")

        effects = engine.reclassify(var, [orf], window)

        assert effects == []

    def test_reverse_frame(self) -> None:
        # Window: "TTCCAT" (length 6), start=0
        # RC: "ATGGAA" → ATG GAA → M E
        # ORF: frame=4, pos=-1 (rc_orf_start=0), dna="ATGGAA"
        # Variant at pos=3 (window idx 2, ref "C"), alt="A"
        # rc_idx = 5 - 2 = 3, offset=3, codon_idx=1, base=0
        # ref_codon="GAA", alt_base=RC("A")="T", alt_codon="TAA" → stop_gain
        seq = "TTCCAT"
        orf = _orf(frame=4, pos=-1, dna="ATGGAA")
        window = _window(seq)
        var = _variant(pos=3, alt="A", classification="Silent")

        effects = engine.reclassify(var, [orf], window)

        assert len(effects) == 1
        assert effects[0].new_class == "Stop Gain"
        assert effects[0].ref_aa == "E"
        assert effects[0].alt_aa == "*"


class TestSummaryAggregate:
    def test_empty(self) -> None:
        result = summary.aggregate([])
        assert result.counts_by_type == {}
        assert result.sankey_data == []

    def test_single_effect(self) -> None:
        orf = _orf(frame=1, pos=1, dna="ATG")
        effect = FrameEffect(
            orf=orf,
            old_class="Silent",
            new_class="Missense",
            ref_aa="M",
            alt_aa="T",
        )
        result = summary.aggregate([effect])
        assert result.counts_by_type == {"Missense": 1}
        assert result.sankey_data == [{"from": "Silent", "to": "Missense", "count": 1}]

    def test_multiple_types(self) -> None:
        orf = _orf(frame=1, pos=1, dna="ATG")
        effects = [
            FrameEffect(orf=orf, old_class="Silent", new_class="Missense", ref_aa="M", alt_aa="T"),
            FrameEffect(orf=orf, old_class="Silent", new_class="Missense", ref_aa="K", alt_aa="S"),
            FrameEffect(orf=orf, old_class="Silent", new_class="Stop Gain", ref_aa="K", alt_aa="*"),
        ]
        result = summary.aggregate(effects)
        assert result.counts_by_type == {"Missense": 2, "Stop Gain": 1}
        sankey = {(d["from"], d["to"]): d["count"] for d in result.sankey_data}
        assert sankey[("Silent", "Missense")] == 2
        assert sankey[("Silent", "Stop Gain")] == 1
