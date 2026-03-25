import pytest

from ghostframe.domain import hmmer

# KRAS partial sequence — verified in API spike to return Ras/PF00071
_KRAS_SEQ = "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSY"


@pytest.mark.integration
@pytest.mark.slow
def test_scan_kras_returns_ras_domain():
    result = hmmer.scan(_KRAS_SEQ)
    assert isinstance(result, list)
    assert any(h.accession == "PF00071" for h in result)


@pytest.mark.integration
@pytest.mark.slow
def test_scan_result_has_valid_fields():
    result = hmmer.scan(_KRAS_SEQ)
    hit = next(h for h in result if h.accession == "PF00071")
    assert hit.name == "Ras"
    assert hit.start >= 1
    assert hit.end > hit.start
    assert isinstance(hit.score, float)


@pytest.mark.integration
@pytest.mark.slow
def test_scan_results_sorted_by_start():
    result = hmmer.scan(_KRAS_SEQ)
    starts = [h.start for h in result]
    assert starts == sorted(starts)
