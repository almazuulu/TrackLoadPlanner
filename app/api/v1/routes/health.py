from fastapi import APIRouter

from app.core.config import settings
from app.models.response import HealthResponse

router = APIRouter()


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the health status of the service."
)
async def health_check() -> HealthResponse:
    """Check the health status of the service.
    
    Returns:
        HealthResponse with status, service name, and version.
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version
    )
