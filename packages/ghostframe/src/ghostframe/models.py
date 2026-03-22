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
    evidence_tier: int = 1  # 1=scan-only, 2=OpenProt-confirmed, 3=SynMICdb-scored
    synmicdb_score: float | None = None


@dataclass
class CodonEffect:
    """Result of comparing a reference codon to an alternate codon."""

    ref_aa: str
    alt_aa: str
    effect_type: str  # "synonymous", "missense", "nonsense"


@dataclass
class ReclassifySummary:
    """Aggregated reclassification statistics."""

    counts_by_type: dict[str, int] = field(default_factory=lambda: {})
    sankey_data: list[dict[str, str | int]] = field(default_factory=lambda: [])


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
class SynMICdbHit:
    """A matching record from the SynMICdb dataset."""

    gene_name: str
    transcript_id: str
    mutation_id: str
    mutation_nt: str  # HGVS-c notation, e.g. "c.375G>T"
    mutation_aa: str
    genome_position: str
    chrom: str
    start: int
    end: int
    strand: str
    frequency: float | None  # Signature-normalized Frequency
    avg_mutation_load: float | None
    alternative_events: str | None
    snp: str | None
    conservation: float | None
    structure_change_score: float | None  # remuRNA
    structure_change_significance: float | None  # RNAsnp
    score: float | None  # SynMICdb Score


@dataclass
class ClinVarHit:
    """A parsed ClinVar record from NCBI E-utilities."""

    accession: str | None
    title: str | None
    germline_significance: str | None
    germline_review_status: str | None
    germline_last_evaluated: str | None
    traits: list[str]
    oncogenicity: str | None
    molecular_consequences: list[str]
    genes: list[str]
    variant_type: str | None


@dataclass
class OpenProtHit:
    """A matching protein from the OpenProt 2.0 database."""

    accession: str
    protein_type: str  # "reference", "novel_isoform", "altORF"
    symbol: str | None
    gene_accession: str | None
    chrom: str | None
    start: int | None
    end: int | None
    strand: int | None  # -1 or 1
    sequence: str | None
    iep: float | None  # isoelectric point
    weight: float | None  # molecular weight (Da)
    uniprot_accessions: str | None  # comma-separated
    segments: str | None  # exon coordinate pairs as JSON string


@dataclass
class EvidenceLookupResult:
    """Aggregated external evidence for a reclassified ORF/variant."""

    openprot: OpenProtHit | None = None
    synmicdb: SynMICdbHit | None = None
    clinvar: ClinVarHit | None = None
    tier: int = 1  # 1=scan-only, 2=OpenProt hit, 3=SynMICdb hit


@dataclass
class DomainHit:
    """A Pfam domain hit from HMMER annotation."""

    accession: str  # e.g. "PF00071"
    name: str  # e.g. "Ras"
    start: int  # 1-based start position in query protein
    end: int  # 1-based end position in query protein
    score: float  # bit score


@dataclass
class ScoredCandidate:
    """A reclassified variant candidate with an aggregate priority score."""

    effect: FrameEffect
    binding: BindingPrediction | None
    domain_hits: list[DomainHit]
    evidence: EvidenceLookupResult | None
    score: float


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
    evidence: EvidenceLookupResult | None
    domain_hits: list[DomainHit] = field(default_factory=lambda: [])
    ranked_candidates: list[ScoredCandidate] = field(default_factory=lambda: [])
    narrative: str | None = None
