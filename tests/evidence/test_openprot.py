import pytest

from ghostframe.evidence import openprot
from ghostframe.models import ORF


@pytest.mark.integration
@pytest.mark.slow
def test_lookup_known_gene_returns_hit():
    orf = ORF(frame=1, pos=1, length=12, dna="ATGAAACGATAA")
    result = openprot.lookup(orf, gene="TP53")
    assert result is not None
    assert result.accession
    assert result.sequence


@pytest.mark.integration
@pytest.mark.slow
def test_lookup_unknown_gene_returns_none():
    orf = ORF(frame=1, pos=1, length=12, dna="ATGAAACGATAA")
    assert openprot.lookup(orf, gene="NOTAREALGENE99999") is None
