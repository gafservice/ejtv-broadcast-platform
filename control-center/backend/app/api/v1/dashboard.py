"""Endpoints REST del dashboard del NOC."""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.core.responses import success_response


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    summary="Obtiene el snapshot actual del dashboard",
    status_code=status.HTTP_200_OK,
)
async def get_dashboard(request: Request) -> dict[str, object]:
    """Retorna temporalmente un snapshot vacío del dashboard."""

    return success_response(
        message="Dashboard endpoint disponible.",
        data={},
        request_id=request.state.request_id,
    )