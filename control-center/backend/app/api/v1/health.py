"""Endpoints de verificación del Backend."""

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.responses import success_response
from app.core.version import API_VERSION, APP_VERSION

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def get_health(request: Request) -> dict[str, object]:
    """Verifica el estado operativo básico del Backend."""

    settings = get_settings()

    return success_response(
        data={
            "status": "healthy",
            "application": settings.app_name,
            "version": APP_VERSION,
            "api_version": API_VERSION,
            "environment": settings.environment,
        },
        message="Backend operativo.",
        request_id=request.state.request_id,
    )
