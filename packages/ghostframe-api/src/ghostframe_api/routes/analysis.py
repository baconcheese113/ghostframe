"""Analysis endpoints — submit jobs and retrieve results."""

from fastapi import APIRouter

from ghostframe_api.schemas import AnalysisRequest, AnalysisResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """Submit a new analysis job."""
    raise NotImplementedError("Analysis endpoint not yet implemented")


@router.get("/results/{job_id}")
async def get_results(job_id: str) -> dict[str, object]:
    """Retrieve results for a completed analysis job."""
    raise NotImplementedError("Results endpoint not yet implemented")
