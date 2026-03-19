"""Tests for MAF parsing, filtering, and normalization."""

from pathlib import Path

from ghostframe.models import Variant
from ghostframe.variants.filters import keep_silent
from ghostframe.variants.maf import parse
from ghostframe.variants.normalize import normalize


class TestMafParse:
    def test_returns_all_variants(self, sample_maf_path: Path) -> None:
        variants = parse(sample_maf_path)
        assert len(variants) == 5

    def test_field_mapping(self, sample_maf_path: Path) -> None:
        variants = parse(sample_maf_path)
        tp53 = next(v for v in variants if v.gene == "TP53")
        assert tp53.gene == "TP53"
        assert tp53.chrom == "17"
        assert tp53.pos == 7577121
        assert tp53.ref == "C"
        assert tp53.alt == "T"
        assert tp53.classification == "Silent"

    def test_skips_comment_lines(self, sample_maf_path: Path) -> None:
        # Comment lines start with '#' — should not appear as variants
        variants = parse(sample_maf_path)
        assert all(not v.gene.startswith("#") for v in variants)

    def test_pos_is_int(self, sample_maf_path: Path) -> None:
        variants = parse(sample_maf_path)
        assert all(isinstance(v.pos, int) for v in variants)

    def test_all_classifications_parsed(self, sample_maf_path: Path) -> None:
        variants = parse(sample_maf_path)
        classifications = {v.classification for v in variants}
        assert classifications == {"Silent", "Missense_Mutation", "Frame_Shift_Del"}


class TestKeepSilent:
    def test_keeps_silent_variants(self, sample_maf_path: Path) -> None:
        variants = parse(sample_maf_path)
        silent = keep_silent(variants)
        assert len(silent) == 3

    def test_excludes_missense(self, sample_maf_path: Path) -> None:
        variants = parse(sample_maf_path)
        silent = keep_silent(variants)
        assert all(v.classification == "Silent" for v in silent)
        assert not any(v.gene == "BRCA1" for v in silent)

    def test_excludes_frameshift(self, sample_maf_path: Path) -> None:
        variants = parse(sample_maf_path)
        silent = keep_silent(variants)
        assert not any(v.gene == "PIK3CA" for v in silent)

    def test_empty_input(self) -> None:
        assert keep_silent([]) == []


class TestNormalize:
    def test_copies_fields(self) -> None:
        v = Variant(chrom="17", pos=7577121, ref="C", alt="T", classification="Silent", gene="TP53")
        nv = normalize(v)
        assert nv.chrom == "17"
        assert nv.pos == 7577121
        assert nv.classification == "Silent"
        assert nv.gene == "TP53"

    def test_strand_default(self) -> None:
        v = Variant(chrom="17", pos=100, ref="A", alt="G", classification="Silent", gene="TP53")
        assert normalize(v).strand == "+"

    def test_alleles_uppercased(self) -> None:
        v = Variant(chrom="17", pos=100, ref="a", alt="g", classification="Silent", gene="TP53")
        nv = normalize(v)
        assert nv.ref == "A"
        assert nv.alt == "G"
