"""Analysis endpoints — submit jobs and retrieve results."""

import uuid
from pathlib import Path

from fastapi import APIRouter

from ghostframe.orfs import find_orfs, parse_file
from ghostframe_api.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    StepResult,
)

router = APIRouter()

_DEMO_FASTA = Path(__file__).parents[6] / "data" / "demo" / "hpv16_k02718.fasta"


@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """Submit a new analysis job, capturing per-step status."""
    job_id = str(uuid.uuid4())[:8]
    steps: list[StepResult] = []

    # Step 1: Parse / load sequence
    try:
        if request.input_type == "sequence" and request.raw_sequence:
            lines = request.raw_sequence.strip().splitlines()
            if lines[0].startswith(">"):
                label = lines[0][1:].split()[0]  # first word of header = record ID
                seq_lines = lines[1:]
            else:
                label = "raw sequence"
                seq_lines = lines
            sequence = "".join(line.strip().upper() for line in seq_lines if line.strip())
        else:
            records = parse_file(_DEMO_FASTA)
            sequence = records[0].sequence
            label = records[0].id
        steps.append(
            StepResult(
                name="MAF / FASTA",
                status="success",
                detail=f"{label} · {len(sequence):,} bp",
            )
        )
    except NotImplementedError:
        steps.append(
            StepResult(
                name="MAF / FASTA",
                status="not_implemented",
                detail="FASTA parsing not yet implemented",
            )
        )
        return AnalysisResponse(
            job_id=job_id, status="partial", steps=steps, error="FASTA parsing not yet implemented"
        )
    except Exception as e:
        steps.append(StepResult(name="MAF / FASTA", status="error", detail=str(e)))
        return AnalysisResponse(
            job_id=job_id, status="error", steps=steps, error="Could not parse input"
        )

    # Step 2: Filter Silent (pass-through in demo mode)
    steps.append(
        StepResult(
            name="Filter Silent",
            status="success",
            detail="Input accepted (demo mode)",
        )
    )

    # Step 3: Seq Fetch (already loaded above)
    steps.append(
        StepResult(
            name="Seq Fetch",
            status="success",
            detail=f"{label} · {len(sequence):,} bp",
        )
    )

    # Step 4: 6-Frame ORF scan
    try:
        orfs = find_orfs(sequence, min_length=request.min_orf_length)
        steps.append(
            StepResult(
                name="6-Frame ORF",
                status="success",
                detail=f"{len(orfs)} ORFs ≥ {request.min_orf_length} bp",
            )
        )
    except NotImplementedError:
        steps.append(
            StepResult(
                name="6-Frame ORF",
                status="not_implemented",
                detail="Awaiting team implementation",
            )
        )
        return AnalysisResponse(
            job_id=job_id,
            status="partial",
            steps=steps,
            error="ORF scan not yet implemented — awaiting team contributions",
        )

    return AnalysisResponse(job_id=job_id, status="complete", steps=steps)


@router.get("/results/{job_id}")
async def get_results(job_id: str) -> dict[str, object]:
    """Retrieve results for a completed analysis job."""
    raise NotImplementedError("Results endpoint not yet implemented")
