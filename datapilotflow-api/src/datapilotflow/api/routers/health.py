"""
Health check endpoints.

Provides health status checks for the API and its dependencies.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str = "1.0.0"
    message: str


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check API health status.

    Returns:
        HealthResponse: API health status
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        message="DataPilotFlow API is running",
    )
