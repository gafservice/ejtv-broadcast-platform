"""Endpoints relacionados con el sistema administrado."""

from dataclasses import asdict

from app.api.serializers import serialize

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_system_service
from app.api.security import require_permission
from app.core.responses import success_response
from app.services.system_service import SystemService

router = APIRouter(
    prefix="/system",
    tags=["System"],
    dependencies=[
        Depends(require_permission("system.read")),
    ],
)


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

@router.get("/resources")
def get_system_resources(
    request: Request,
    service: SystemService = Depends(get_system_service),
) -> dict[str, object]:
    """Retorna el estado actual de los recursos del servidor."""

    resources = service.get_system_resources()

    return success_response(
        data=serialize(resources),
        message="Recursos del sistema obtenidos correctamente.",
        request_id=request.state.request_id,
    )

@router.get("/services")
def get_service_monitoring(
    request: Request,
    service: SystemService = Depends(get_system_service),
) -> dict[str, object]:
    """Retorna el estado actual de los servicios monitoreados."""

    monitoring = service.get_service_monitoring()

    return success_response(
        data=serialize(monitoring),
        message="Servicios monitoreados obtenidos correctamente.",
        request_id=request.state.request_id,
    )
