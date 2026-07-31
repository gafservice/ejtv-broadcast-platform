"""Endpoints REST del dashboard."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.security import require_permission
from app.core.responses import success_response
from app.domain.identity.entities import AuthenticatedIdentity


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    summary="Obtiene el estado del dashboard",
    status_code=status.HTTP_200_OK,
)
def get_dashboard(
    request: Request,
    identity: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("dashboard.view")),
    ],
) -> dict[str, object]:
    """Confirma que el dashboard está disponible para el usuario."""

    return success_response(
        message="Dashboard endpoint disponible.",
        data={
            "authenticated_user": {
                "id": str(identity.user_id),
                "username": identity.username.value,
                "roles": sorted(
                    role.value for role in identity.roles
                ),
                "permissions": sorted(
                    permission.value
                    for permission in identity.permissions
                ),
            },
        },
        request_id=request.state.request_id,
    )
