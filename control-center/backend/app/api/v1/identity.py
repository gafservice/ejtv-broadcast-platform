"""Endpoints administrativos del subsistema Identity."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import (
    get_identity_administration_service,
)
from app.api.schemas.identity_administration import (
    AssignUserRoleRequest,
    ChangeUserPasswordRequest,
    ChangeUserStatusRequest,
    CreateUserRequest,
    RoleListResponse,
    RoleResponse,
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


def _serialize_role(role) -> RoleResponse:
    """Convierte una entidad Role en una respuesta pública."""

    return RoleResponse(
        name=role.name.value,
        permissions=sorted(
            permission.name.value
            for permission in role.permissions
        ),
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


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("users.read")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Obtiene un usuario por identificador."""

    user = service.get_user(
        actor=actor,
        user_id=user_id,
    )

    return success_response(
        data=_serialize_user(user).model_dump(),
        message="Usuario obtenido correctamente.",
        request_id=request.state.request_id,
    )


@router.patch("/users/{user_id}/status")
def change_user_status(
    user_id: str,
    payload: ChangeUserStatusRequest,
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("users.manage")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Cambia el estado operativo de un usuario."""

    user = service.change_user_status(
        actor=actor,
        user_id=user_id,
        status=payload.status,
    )

    return success_response(
        data=_serialize_user(user).model_dump(),
        message="Estado del usuario actualizado correctamente.",
        request_id=request.state.request_id,
    )


@router.post("/users/{user_id}/password")
def change_user_password(
    user_id: str,
    payload: ChangeUserPasswordRequest,
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("users.manage")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Cambia administrativamente la contraseña de un usuario."""

    user = service.change_password(
        actor=actor,
        user_id=user_id,
        password=payload.password,
    )

    return success_response(
        data=_serialize_user(user).model_dump(),
        message="Contraseña del usuario actualizada correctamente.",
        request_id=request.state.request_id,
    )


@router.get("/roles")
def list_roles(
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("roles.read")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Lista los roles canónicos disponibles."""

    roles = service.list_roles(actor=actor)

    response = RoleListResponse(
        roles=[
            _serialize_role(role)
            for role in roles
        ],
        total=len(roles),
    )

    return success_response(
        data=response.model_dump(),
        message="Roles obtenidos correctamente.",
        request_id=request.state.request_id,
    )


@router.post("/users/{user_id}/roles")
def assign_role(
    user_id: str,
    payload: AssignUserRoleRequest,
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("roles.write")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Asigna un rol canónico a un usuario."""

    user = service.assign_role(
        actor=actor,
        user_id=user_id,
        role_name=payload.role_name,
    )

    return success_response(
        data=_serialize_user(user).model_dump(),
        message="Rol asignado correctamente.",
        request_id=request.state.request_id,
    )


@router.delete(
    "/users/{user_id}/roles/{role_name}"
)
def remove_role(
    user_id: str,
    role_name: str,
    request: Request,
    actor: Annotated[
        AuthenticatedIdentity,
        Depends(require_permission("roles.write")),
    ],
    service: IdentityAdministrationService = Depends(
        get_identity_administration_service
    ),
) -> dict[str, object]:
    """Revoca un rol canónico de un usuario."""

    user = service.remove_role(
        actor=actor,
        user_id=user_id,
        role_name=role_name,
    )

    return success_response(
        data=_serialize_user(user).model_dump(),
        message="Rol revocado correctamente.",
        request_id=request.state.request_id,
    )

