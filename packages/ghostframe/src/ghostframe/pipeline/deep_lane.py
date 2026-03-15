"""Deep lane pipeline — background, per-variant enrichment.

peptide generation → MHC binding prediction → domain annotation →
external evidence linking → structured report.

Triggered per-variant on user click in the dashboard.
"""

from ghostframe.models import ORF, DeepLaneResult, NormalizedVariant


def run(
    variant: NormalizedVariant,
    orfs: list[ORF],
    hla_alleles: list[str] | None = None,
) -> DeepLaneResult:
    """Run deep analysis for a single reclassified variant.

    Args:
        variant: The variant to analyze in depth.
        orfs: Overlapping ORFs from the fast lane.
        hla_alleles: Optional list of HLA alleles for MHC prediction.

    Returns:
        DeepLaneResult with peptides, binding predictions, evidence,
        and optional narrative summary.
    """
    raise NotImplementedError("Deep lane pipeline not yet implemented")
