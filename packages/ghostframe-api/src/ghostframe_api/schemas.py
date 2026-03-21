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
    new_class: str  # "Missense" | "Stop Gain" | "Start Loss"
    ref_codon: str
    alt_codon: str
    ref_aa: str
    alt_aa: str
    evidence_tier: int
    synmicdb_score: float | None
    narrative: str
    peptides: list[PeptideResponse]


class AnalysisSummary(BaseModel):
    total_silent: int
    reclassified: int
    frames_affected: int
    best_ic50: float | None


class StepResult(BaseModel):
    name: str
    status: str  # "success" | "error" | "not_implemented" | "skipped"
    detail: str


class AnalysisRequest(BaseModel):
    """Request to start an analysis job."""

    accession: str = "K02718.1"
    use_demo: bool = True
    min_orf_length: int = 50
    input_type: str = "accession"  # "accession" | "sequence"
    raw_sequence: str | None = None  # populated when input_type == "sequence"


class AnalysisResponse(BaseModel):
    """Response with analysis job status and results."""

    job_id: str
    status: str  # "complete" | "partial" | "error"
    steps: list[StepResult] = []
    summary: AnalysisSummary | None = None
    variants: list[FrameEffectResponse] = []
    error: str | None = None
