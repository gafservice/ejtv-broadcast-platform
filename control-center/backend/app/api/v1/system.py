"""Endpoints relacionados con el sistema administrado."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_system_service
from app.core.responses import success_response
from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info")
def get_system_info(
    request: Request,
    service: SystemService = Depends(get_system_service),
) -> dict[str, object]:
    """Retorna la identidad básica del servidor administrado."""

    system_info = service.get_system_info()

    return success_response(
        data=asdict(system_info),
        message="Información del sistema obtenida correctamente.",
        request_id=request.state.request_id,
    )
