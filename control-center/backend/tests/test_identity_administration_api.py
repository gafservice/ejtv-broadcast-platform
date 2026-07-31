"""Pruebas HTTP de administración de usuarios Identity."""

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_identity_administration_service,
)
from app.api.security import get_current_identity
from app.domain.identity.entities import (
    AuthenticatedIdentity,
    User,
)
from app.domain.identity.exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
)
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.main import app


class FakeIdentityAdministrationService:
    """Servicio administrativo controlado para pruebas HTTP."""

    def __init__(
        self,
        *,
        users: tuple[User, ...] = (),
        create_error: Exception | None = None,
    ) -> None:
        self.users = users
        self.create_error = create_error
        self.received_actor: AuthenticatedIdentity | None = None
        self.received_username: str | None = None
        self.received_email: str | None = None
        self.received_password: str | None = None

    def create_user(
        self,
        *,
        actor: AuthenticatedIdentity,
        username: str,
        email: str,
        password: str,
    ) -> User:
        self.received_actor = actor
        self.received_username = username
        self.received_email = email
        self.received_password = password

        if self.create_error is not None:
            raise self.create_error

        return User(
            id=UserId(
                UUID(
                    "01900000-0000-7000-8000-000000000201"
                )
            ),
            username=Username(username),
            email=Email(email),
            password_hash=PasswordHash(
                "$2b$12$abcdefghijklmnopqrstuu"
                "abcdefghijklmnopqrstuu1234567890"
            ),
        )

    def list_users(
        self,
        *,
        actor: AuthenticatedIdentity,
    ) -> tuple[User, ...]:
        self.received_actor = actor
        return self.users


def make_actor(
    *permissions: str,
) -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        user_id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000200"
            )
        ),
        username=Username("administrator"),
        roles=frozenset(
            {
                RoleName("administrator"),
            }
        ),
        permissions=frozenset(
            PermissionName(permission)
            for permission in permissions
        ),
    )


def make_user(
    *,
    user_id: str,
    username: str,
    email: str,
) -> User:
    return User(
        id=UserId(UUID(user_id)),
        username=Username(username),
        email=Email(email),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Aísla las dependencias modificadas por cada prueba."""

    previous_service = app.dependency_overrides.get(
        get_identity_administration_service
    )
    previous_identity = app.dependency_overrides.get(
        get_current_identity
    )

    with TestClient(app) as test_client:
        yield test_client

    if previous_service is None:
        app.dependency_overrides.pop(
            get_identity_administration_service,
            None,
        )
    else:
        app.dependency_overrides[
            get_identity_administration_service
        ] = previous_service

    if previous_identity is None:
        app.dependency_overrides.pop(
            get_current_identity,
            None,
        )
    else:
        app.dependency_overrides[
            get_current_identity
        ] = previous_identity


def configure_dependencies(
    *,
    service: FakeIdentityAdministrationService,
    identity: AuthenticatedIdentity,
) -> None:
    app.dependency_overrides[
        get_identity_administration_service
    ] = lambda: service

    app.dependency_overrides[
        get_current_identity
    ] = lambda: identity


def test_create_user_returns_created_user(
    client: TestClient,
) -> None:
    actor = make_actor("users.write")
    service = FakeIdentityAdministrationService()

    configure_dependencies(
        service=service,
        identity=actor,
    )

    response = client.post(
        "/api/v1/identity/users",
        json={
            "username": "noc_operator",
            "email": "operator@example.com",
            "password": "secure-password",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"] == {
        "user_id": (
            "01900000-0000-7000-8000-000000000201"
        ),
        "username": "noc_operator",
        "email": "operator@example.com",
        "status": "active",
        "roles": [],
    }
    assert payload["message"] == (
        "Usuario creado correctamente."
    )

    assert service.received_actor == actor
    assert service.received_username == "noc_operator"
    assert service.received_email == (
        "operator@example.com"
    )
    assert service.received_password == "secure-password"


def test_list_users_returns_public_user_data(
    client: TestClient,
) -> None:
    actor = make_actor("users.read")

    service = FakeIdentityAdministrationService(
        users=(
            make_user(
                user_id=(
                    "01900000-0000-7000-8000-000000000202"
                ),
                username="alpha-user",
                email="alpha@example.com",
            ),
            make_user(
                user_id=(
                    "01900000-0000-7000-8000-000000000203"
                ),
                username="zeta-user",
                email="zeta@example.com",
            ),
        )
    )

    configure_dependencies(
        service=service,
        identity=actor,
    )

    response = client.get(
        "/api/v1/identity/users"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["total"] == 2
    assert [
        user["username"]
        for user in payload["data"]["users"]
    ] == [
        "alpha-user",
        "zeta-user",
    ]

    assert all(
        "password_hash" not in user
        for user in payload["data"]["users"]
    )


@pytest.mark.parametrize(
    (
        "error",
        "expected_code",
    ),
    [
        (
            UsernameAlreadyExists(),
            "USERNAME_ALREADY_EXISTS",
        ),
        (
            EmailAlreadyExists(),
            "EMAIL_ALREADY_EXISTS",
        ),
    ],
)
def test_create_user_translates_duplicate_errors(
    client: TestClient,
    error: Exception,
    expected_code: str,
) -> None:
    service = FakeIdentityAdministrationService(
        create_error=error
    )

    configure_dependencies(
        service=service,
        identity=make_actor("users.write"),
    )

    response = client.post(
        "/api/v1/identity/users",
        json={
            "username": "duplicate-user",
            "email": "duplicate@example.com",
            "password": "secure-password",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        expected_code
    )


@pytest.mark.parametrize(
    (
        "method",
        "path",
    ),
    [
        (
            "post",
            "/api/v1/identity/users",
        ),
        (
            "get",
            "/api/v1/identity/users",
        ),
    ],
)
def test_identity_user_routes_require_authentication(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    request = getattr(client, method)

    arguments: dict[str, object] = {}

    if method == "post":
        arguments["json"] = {
            "username": "operator",
            "email": "operator@example.com",
            "password": "secure-password",
        }

    response = request(path, **arguments)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == (
        "Bearer"
    )
    assert response.json()["error"]["code"] == (
        "HTTP_401"
    )


def test_create_user_requires_users_write(
    client: TestClient,
) -> None:
    configure_dependencies(
        service=FakeIdentityAdministrationService(),
        identity=make_actor("users.read"),
    )

    response = client.post(
        "/api/v1/identity/users",
        json={
            "username": "operator",
            "email": "operator@example.com",
            "password": "secure-password",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "PERMISSION_DENIED"
    )


def test_list_users_requires_users_read(
    client: TestClient,
) -> None:
    configure_dependencies(
        service=FakeIdentityAdministrationService(),
        identity=make_actor("users.write"),
    )

    response = client.get(
        "/api/v1/identity/users"
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "PERMISSION_DENIED"
    )


def test_identity_user_routes_are_registered_in_openapi(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    operations = response.json()["paths"][
        "/api/v1/identity/users"
    ]

    assert operations["post"]["security"] == [
        {
            "BearerAuth": [],
        }
    ]

    assert operations["get"]["security"] == [
        {
            "BearerAuth": [],
        }
    ]

    assert "Identity Administration" in (
        operations["post"]["tags"]
    )
    assert "Identity Administration" in (
        operations["get"]["tags"]
    )
