"""OpenProt alternative ORF annotation lookup.

Checks whether discovered ORFs match known alternative ORFs in the
OpenProt 2.0 database.

Pipeline position: reclassify → [evidence.openprot] → reports
"""

from ghostframe.models import ORF


def lookup(orf: ORF) -> dict[str, object] | None:
    """Look up an ORF in the OpenProt database.

    Args:
        orf: ORF with genomic coordinates to search for.

    Returns:
        Match record dict if found, None otherwise.
    """
    raise NotImplementedError("OpenProt lookup not yet implemented")
