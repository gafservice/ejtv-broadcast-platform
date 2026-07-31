"""Dependencias HTTP de autenticación y autorización."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.api.dependencies import (
    get_authorization_service,
    get_token_provider,
)
from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.protocols import TokenProvider
from app.domain.identity.value_objects import PermissionName
from app.services.authorization_service import AuthorizationService


_bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="Token JWT obtenido mediante /api/v1/auth/login.",
)


def _authentication_error() -> HTTPException:
    """Construye la respuesta HTTP estándar para autenticación inválida."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Se requiere un token de acceso válido.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_identity(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    token_provider: Annotated[
        TokenProvider,
        Depends(get_token_provider),
    ],
) -> AuthenticatedIdentity:
    """Obtiene la identidad representada por el JWT Bearer."""

    if credentials is None:
        raise _authentication_error()

    if credentials.scheme.lower() != "bearer":
        raise _authentication_error()

    identity = token_provider.verify(credentials.credentials)

    if identity is None:
        raise _authentication_error()

    return identity


def require_permission(
    permission: str,
) -> Callable[..., AuthenticatedIdentity]:
    """Crea una dependencia que exige un permiso determinado."""

    permission_name = PermissionName(permission)

    def dependency(
        identity: Annotated[
            AuthenticatedIdentity,
            Depends(get_current_identity),
        ],
        authorization_service: Annotated[
            AuthorizationService,
            Depends(get_authorization_service),
        ],
    ) -> AuthenticatedIdentity:
        authorization_service.authorize(
            identity=identity,
            permission=permission_name.value,
        )

        return identity

    return dependency
