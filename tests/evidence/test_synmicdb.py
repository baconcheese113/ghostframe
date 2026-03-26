from pathlib import Path

import pytest

from ghostframe.evidence import synmicdb
from ghostframe.models import NormalizedVariant


@pytest.mark.integration
def test_lookup_known_tp53_variant():
    v = NormalizedVariant(
        chrom="17",
        pos=7675994,
        ref="G",
        alt="T",
        classification="Silent",
        gene="TP53",
    )
    result = synmicdb.lookup(v)
    assert result is not None
    assert result.gene_name == "TP53"
    assert result.mutation_nt == "c.375G>T"
    assert result.score is not None


@pytest.mark.integration
def test_lookup_bogus_position_returns_none():
    v = NormalizedVariant(
        chrom="1",
        pos=1,
        ref="A",
        alt="T",
        classification="Silent",
        gene="UNKNOWN",
    )
    assert synmicdb.lookup(v) is None


def test_load_raises_file_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(synmicdb, "_DATA_REF", tmp_path / "missing.csv.zip")
    monkeypatch.setattr(synmicdb, "_cache", None)
    with pytest.raises(FileNotFoundError, match="SynMICdb dataset not found"):
        synmicdb.lookup(
            NormalizedVariant(
                chrom="1",
                pos=1,
                ref="A",
                alt="T",
                classification="Silent",
                gene="X",
            )
        )
