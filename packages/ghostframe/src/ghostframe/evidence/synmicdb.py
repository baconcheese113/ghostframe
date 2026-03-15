"""SynMICdb synonymous mutation lookup.

Checks variant recurrence and scores in the SynMICdb database of
synonymous mutations in cancer.

Pipeline position: reclassify → [evidence.synmicdb] → reports
"""

from ghostframe.models import Variant


def lookup(variant: Variant) -> dict[str, object] | None:
    """Look up a variant in SynMICdb.

    Args:
        variant: Variant to search for.

    Returns:
        SynMICdb record dict if found, None otherwise.
    """
    raise NotImplementedError("SynMICdb lookup not yet implemented")
