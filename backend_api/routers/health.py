"""backend_api/routers/health.py -- liveness check, no data access."""
from fastapi import APIRouter

from backend_api.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Basic liveness check. Does not touch any frozen data or model."""
    return HealthResponse(status="ok", service="VENTORA API")
