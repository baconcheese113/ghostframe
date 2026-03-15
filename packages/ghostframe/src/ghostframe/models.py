"""Shared data models for the GhostFrame library.

All models are plain dataclasses — no Pydantic in the core library.
Pydantic is used only at the API boundary (ghostframe-api/schemas.py).
"""

from dataclasses import dataclass, field


@dataclass
class FastaRecord:
    """A single sequence from a FASTA file."""

    id: str
    description: str
    sequence: str


@dataclass
class ORF:
    """An open reading frame found by the scanner."""

    frame: int  # 1-6
    pos: int  # 1-based for forward frames, negative for reverse frames
    length: int  # length in bases (includes stop codon)
    dna: str  # the ORF DNA sequence


# --- Stubbed models for future modules ---


@dataclass
class Variant:
    """A somatic variant from a MAF or VCF file."""

    chrom: str
    pos: int
    ref: str
    alt: str
    classification: str  # e.g. "Silent", "Missense_Mutation"
    gene: str


@dataclass
class NormalizedVariant:
    """A variant with standardized coordinates and alleles."""

    chrom: str
    pos: int
    ref: str
    alt: str
    classification: str
    gene: str
    strand: str = "+"


@dataclass
class GenomicWindow:
    """A reference sequence window around a variant."""

    chrom: str
    start: int
    end: int
    sequence: str


@dataclass
class FrameEffect:
    """The effect of a variant in a specific ORF frame."""

    orf: ORF
    old_class: str  # original classification (e.g. "Silent")
    new_class: str  # reclassified (e.g. "Missense")
    ref_aa: str
    alt_aa: str


@dataclass
class CodonEffect:
    """Result of comparing a reference codon to an alternate codon."""

    ref_aa: str
    alt_aa: str
    effect_type: str  # "synonymous", "missense", "nonsense"


@dataclass
class ReclassifySummary:
    """Aggregated reclassification statistics."""

    counts_by_type: dict[str, int] = field(default_factory=dict)
    sankey_data: list[dict[str, str | int]] = field(default_factory=list)


@dataclass
class Peptide:
    """A peptide generated from a translated ORF."""

    sequence: str
    start: int
    k: int


@dataclass
class BindingPrediction:
    """MHC binding prediction for a peptide."""

    peptide: Peptide
    allele: str
    affinity: float
    rank: float


@dataclass
class FastLaneResult:
    """Result of the fast lane pipeline."""

    summary: ReclassifySummary
    sankey_data: list[dict[str, str | int]]
    reclassified_variants: list[FrameEffect]


@dataclass
class DeepLaneResult:
    """Result of the deep lane pipeline for a single variant."""

    peptides: list[Peptide]
    binding_predictions: list[BindingPrediction]
    evidence: dict[str, object]
    narrative: str | None = None
