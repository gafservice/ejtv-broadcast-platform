"""Endpoints administrativos del subsistema Identity."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import (
    get_identity_administration_service,
)
from app.api.schemas.identity_administration import (
    CreateUserRequest,
    UserListResponse,
    UserResponse,
)
from app.api.security import (
    get_current_identity,
    require_permission,
)
from app.core.responses import success_response
from app.domain.identity.entities import (
    AuthenticatedIdentity,
    User,
)
from app.services.identity_administration_service import (
    IdentityAdministrationService,
)


router = APIRouter(
    prefix="/identity",
    tags=["Identity Administration"],
)


def _serialize_user(user: User) -> UserResponse:
    """Convierte una entidad User en una respuesta pública."""

    return UserResponse(
        user_id=str(user.id),
        username=user.username.value,
        email=user.email.value,
        status=user.status,
        roles=sorted(
            role.name.value
            for role in user.roles
        ),
    )


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: CreateUserRequest,
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("users.write")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Crea un usuario administrado."""

    user = service.create_user(
        actor=actor,
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )

    return success_response(
        data=_serialize_user(user).model_dump(),
        message="Usuario creado correctamente.",
        request_id=request.state.request_id,
    )


@router.get("/users")
def list_users(
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("users.read")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Lista los usuarios administrados."""

    users = service.list_users(actor=actor)

    response = UserListResponse(
        users=[
            _serialize_user(user)
            for user in users
        ],
        total=len(users),
    )

    return success_response(
        data=response.model_dump(),
        message="Usuarios obtenidos correctamente.",
        request_id=request.state.request_id,
    )
