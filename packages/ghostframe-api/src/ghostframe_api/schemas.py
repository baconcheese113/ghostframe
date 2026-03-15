"""Pydantic request/response models for the API layer.

Pydantic is used ONLY here at the API boundary — the core library
uses plain dataclasses.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response for the health check endpoint."""

    status: str
    version: str


class AnalysisRequest(BaseModel):
    """Request to start an analysis job."""

    # Stubbed — will include file reference, parameters, etc.
    min_orf_length: int = 50


class AnalysisResponse(BaseModel):
    """Response with analysis job status."""

    job_id: str
    status: str
