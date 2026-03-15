"""ClinVar variant significance lookup.

Checks clinical significance of variants in the ClinVar database.

Pipeline position: reclassify → [evidence.clinvar] → reports
"""

from ghostframe.models import Variant


def lookup(variant: Variant) -> dict[str, object] | None:
    """Look up a variant in ClinVar.

    Args:
        variant: Variant to search for.

    Returns:
        ClinVar record dict if found, None otherwise.
    """
    raise NotImplementedError("ClinVar lookup not yet implemented")
