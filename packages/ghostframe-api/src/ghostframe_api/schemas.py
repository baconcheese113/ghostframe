"""Pydantic request/response models for the API layer.

Pydantic is used ONLY here at the API boundary — the core library
uses plain dataclasses.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response for the health check endpoint."""

    status: str
    version: str


class PeptideResponse(BaseModel):
    sequence: str
    allele: str
    ic50: float
    rank: float


class FrameEffectResponse(BaseModel):
    id: str
    gene: str
    position: int
    frame: int
    old_class: str
    new_class: str
    ref_codon: str = ""
    alt_codon: str = ""
    ref_aa: str
    alt_aa: str
    evidence_tier: int
    synmicdb_score: float | None
    narrative: str = ""
    peptides: list[PeptideResponse] = []
    # ORF track fields for ReadingFrameViewer
    orf_dna: str = ""
    orf_pos: int = 1
    orf_length: int = 0
    window_size: int = 1001
    variant_in_window: int = 500
    codon_pos: int | None = None
    chrom: str = ""
    ref: str = ""
    alt: str = ""


class AnalysisSummary(BaseModel):
    total_input_variants: int
    total_silent_variants: int
    total_orfs: int
    total_effects: int
    reclassified_effects: int
    total_silent: int
    reclassified: int
    frames_affected: int
    best_ic50: float | None


class StepResult(BaseModel):
    name: str
    status: str  # "success" | "error" | "not_implemented" | "skipped" | "running"
    detail: str
    progress_current: int | None = None
    progress_total: int | None = None


class AnalysisRequest(BaseModel):
    """Request to start an analysis job."""

    maf_content: str | None = None  # raw MAF text; None = use demo
    maf_filename: str | None = None
    min_orf_length: int = 50


# Deep lane response types

class DomainHitResponse(BaseModel):
    accession: str
    name: str
    start: int
    end: int
    score: float


class EvidenceResponse(BaseModel):
    tier: int
    openprot_accession: str | None = None
    openprot_type: str | None = None
    synmicdb_score: float | None = None
    clinvar_significance: str | None = None


class ScoredCandidateResponse(BaseModel):
    peptide_sequence: str | None
    allele: str | None
    ic50: float | None
    rank: float | None
    score: float
    domain_hits: list[DomainHitResponse] = []
