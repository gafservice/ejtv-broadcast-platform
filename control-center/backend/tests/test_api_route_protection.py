"""Pruebas de autenticación y autorización de rutas privadas."""

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_authorization_service,
    get_token_provider,
)
from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.exceptions import PermissionDenied
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.main import app


class FakeTokenProvider:
    """Proveedor controlado para validar tokens HTTP."""

    def __init__(
        self,
        identity: AuthenticatedIdentity | None,
    ) -> None:
        self._identity = identity

    def issue(
        self,
        identity: AuthenticatedIdentity,
    ) -> str:
        return "valid-token"

    def verify(
        self,
        token: str,
    ) -> AuthenticatedIdentity | None:
        if token != "valid-token":
            return None

        return self._identity


class FakeAuthorizationService:
    """Autoriza según los permisos contenidos en la identidad."""

    def authorize(
        self,
        *,
        identity: AuthenticatedIdentity,
        permission: str,
    ) -> None:
        if not identity.has_permission(
            PermissionName(permission)
        ):
            raise PermissionDenied


def make_identity(
    *permissions: str,
) -> AuthenticatedIdentity:
    """Construye una identidad con permisos explícitos."""

    return AuthenticatedIdentity(
        user_id=UserId(
            UUID("01900000-0000-7000-8000-000000000099")
        ),
        username=Username("securitytester"),
        roles=frozenset(
            {
                RoleName("operator"),
            }
        ),
        permissions=frozenset(
            PermissionName(permission)
            for permission in permissions
        ),
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Proporciona un cliente y restaura los overrides."""

    previous_token_provider = app.dependency_overrides.get(
        get_token_provider
    )
    previous_authorization_service = (
        app.dependency_overrides.get(
            get_authorization_service
        )
    )

    with TestClient(app) as test_client:
        yield test_client

    if previous_token_provider is None:
        app.dependency_overrides.pop(
            get_token_provider,
            None,
        )
    else:
        app.dependency_overrides[
            get_token_provider
        ] = previous_token_provider

    if previous_authorization_service is None:
        app.dependency_overrides.pop(
            get_authorization_service,
            None,
        )
    else:
        app.dependency_overrides[
            get_authorization_service
        ] = previous_authorization_service


def configure_security(
    identity: AuthenticatedIdentity | None,
) -> None:
    """Configura dependencias controladas de seguridad."""

    app.dependency_overrides[
        get_token_provider
    ] = lambda: FakeTokenProvider(identity)

    app.dependency_overrides[
        get_authorization_service
    ] = lambda: FakeAuthorizationService()


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard",
        "/api/v1/system/info",
        "/api/v1/system/resources",
        "/api/v1/system/services",
    ],
)
def test_private_routes_reject_missing_token(
    client: TestClient,
    path: str,
) -> None:
    response = client.get(path)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "HTTP_401"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard",
        "/api/v1/system/info",
    ],
)
def test_private_routes_reject_invalid_token(
    client: TestClient,
    path: str,
) -> None:
    configure_security(
        make_identity(
            "dashboard.read",
            "system.read",
        )
    )

    response = client.get(
        path,
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "HTTP_401"


def test_dashboard_rejects_missing_permission(
    client: TestClient,
) -> None:
    configure_security(
        make_identity("system.read")
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": "Bearer valid-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "PERMISSION_DENIED"
    )


def test_system_rejects_missing_permission(
    client: TestClient,
) -> None:
    configure_security(
        make_identity("dashboard.read")
    )

    response = client.get(
        "/api/v1/system/info",
        headers={
            "Authorization": "Bearer valid-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "PERMISSION_DENIED"
    )


def test_dashboard_accepts_authorized_identity(
    client: TestClient,
) -> None:
    configure_security(
        make_identity("dashboard.read")
    )

    response = client.get(
        "/api/v1/dashboard",
        headers={
            "Authorization": "Bearer valid-token",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"][
        "authenticated_user"
    ]["username"] == "securitytester"
