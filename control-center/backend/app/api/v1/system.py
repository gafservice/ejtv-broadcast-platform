"""Endpoints relacionados con el sistema administrado."""

from dataclasses import asdict, is_dataclass

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_system_service
from app.core.responses import success_response
from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["System"])

def serialize_dataclass(value):
    """Convierte recursivamente dataclasses en diccionarios."""

    if is_dataclass(value):
        return {
            key: serialize_dataclass(val)
            for key, val in asdict(value).items()
        }

    if isinstance(value, dict):
        return {
            key: serialize_dataclass(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [
            serialize_dataclass(item)
            for item in value
        ]

    return value


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
        data=serialize_dataclass(resources),
        message="Recursos del sistema obtenidos correctamente.",
        request_id=request.state.request_id,
    )
