import pytest

from ghostframe.evidence import clinvar
from ghostframe.models import NormalizedVariant


@pytest.mark.integration
@pytest.mark.slow
def test_lookup_known_variant_returns_parsed_hit():
    v = NormalizedVariant(
        chrom="13",
        pos=32333065,
        ref="A",
        alt="AA",
        classification="Silent",
        gene="BRCA2",
    )
    result = clinvar.lookup(v)
    assert result is not None
    assert result.accession is not None
    assert result.germline_significance is not None
    assert isinstance(result.traits, list)


@pytest.mark.integration
@pytest.mark.slow
def test_lookup_bogus_position_returns_none():
    v = NormalizedVariant(
        chrom="99",
        pos=999999999,
        ref="A",
        alt="T",
        classification="Silent",
        gene="UNKNOWN",
    )
    assert clinvar.lookup(v) is None
