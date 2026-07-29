"""Endpoints REST del dashboard."""

from fastapi import APIRouter, Request, status

from app.core.responses import success_response


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    summary="Obtiene el estado del dashboard",
    status_code=status.HTTP_200_OK,
)
def get_dashboard(request: Request) -> dict[str, object]:
    """Confirma que el endpoint del dashboard está disponible."""

    return success_response(
        message="Dashboard endpoint disponible.",
        data={},
        request_id=request.state.request_id,
    )