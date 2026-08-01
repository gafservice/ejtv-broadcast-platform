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
        operation_error: Exception | None = None,
    ) -> None:
        self.users = users
        self.create_error = create_error
        self.operation_error = operation_error
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


    def change_user_status(
        self,
        *,
        actor,
        user_id,
        status,
    ):
        if self.operation_error is not None:
            raise self.operation_error

        return make_user(
            user_id=user_id,
        )

    def list_users(
        self,
        *,
        actor: AuthenticatedIdentity,
    ) -> tuple[User, ...]:
        self.received_actor = actor
        return self.users


    def list_permissions(
        self,
        *,
        actor: AuthenticatedIdentity,
    ) -> tuple[str, ...]:
        self.received_actor = actor

        if self.operation_error is not None:
            raise self.operation_error

        return (
            "alarms.read",
            "dashboard.read",
            "roles.read",
        )

    def list_roles(
        self,
        *,
        actor: AuthenticatedIdentity,
    ):
        from app.domain.identity.entities import (
            Permission,
            Role,
        )
        from app.domain.identity.value_objects import (
            PermissionName,
            RoleName,
        )

        self.received_actor = actor

        if self.operation_error is not None:
            raise self.operation_error

        return (
            Role(
                name=RoleName("administrator"),
                permissions=frozenset(
                    {
                        Permission(
                            name=PermissionName(
                                "users.manage"
                            )
                        )
                    }
                ),
            ),
            Role(
                name=RoleName("operator"),
                permissions=frozenset(
                    {
                        Permission(
                            name=PermissionName(
                                "streaming.read"
                            )
                        )
                    }
                ),
            ),
            Role(
                name=RoleName("viewer"),
                permissions=frozenset(
                    {
                        Permission(
                            name=PermissionName(
                                "dashboard.read"
                            )
                        )
                    }
                ),
            ),
        )

    def assign_role(
        self,
        *,
        actor: AuthenticatedIdentity,
        user_id: str,
        role_name: str,
    ) -> User:
        from app.domain.identity.entities import Role
        from app.domain.identity.value_objects import RoleName

        self.received_actor = actor

        if self.operation_error is not None:
            raise self.operation_error

        return self.users[0].with_role(
            Role(
                name=RoleName(role_name)
            )
        )

    def remove_role(
        self,
        *,
        actor: AuthenticatedIdentity,
        user_id: str,
        role_name: str,
    ) -> User:
        from app.domain.identity.value_objects import RoleName

        self.received_actor = actor

        if self.operation_error is not None:
            raise self.operation_error

        return self.users[0].without_role(
            RoleName(role_name)
        )


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


def test_list_roles_returns_canonical_roles(
    client: TestClient,
) -> None:
    configure_dependencies(
        service=FakeIdentityAdministrationService(),
        identity=make_actor("roles.read"),
    )

    response = client.get(
        "/api/v1/identity/roles"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["total"] == 3
    assert [
        role["name"]
        for role in payload["data"]["roles"]
    ] == [
        "administrator",
        "operator",
        "viewer",
    ]


def test_assign_role_returns_updated_user(
    client: TestClient,
) -> None:
    user = make_user(
        user_id=(
            "01900000-0000-7000-8000-000000000210"
        ),
        username="role-user",
        email="role-user@example.com",
    )

    configure_dependencies(
        service=FakeIdentityAdministrationService(
            users=(user,)
        ),
        identity=make_actor("roles.write"),
    )

    response = client.post(
        f"/api/v1/identity/users/{user.id}/roles",
        json={
            "role_name": "operator",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["roles"] == [
        "operator",
    ]
    assert payload["message"] == (
        "Rol asignado correctamente."
    )


def test_remove_role_returns_updated_user(
    client: TestClient,
) -> None:
    from app.domain.identity.entities import Role
    from app.domain.identity.value_objects import RoleName

    user = User(
        id=UserId(
            UUID(
                "01900000-0000-7000-8000-000000000211"
            )
        ),
        username=Username("viewer-user"),
        email=Email("viewer-user@example.com"),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=frozenset(
            {
                Role(
                    name=RoleName("viewer")
                )
            }
        ),
    )

    configure_dependencies(
        service=FakeIdentityAdministrationService(
            users=(user,)
        ),
        identity=make_actor("roles.write"),
    )

    response = client.delete(
        (
            f"/api/v1/identity/users/{user.id}"
            "/roles/viewer"
        )
    )

    assert response.status_code == 200
    assert response.json()["data"]["roles"] == []
    assert response.json()["message"] == (
        "Rol revocado correctamente."
    )


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "payload",
    ),
    [
        (
            "post",
            (
                "/api/v1/identity/users/"
                "01900000-0000-7000-8000-000000000212"
                "/roles"
            ),
            {"role_name": "unknown-role"},
        ),
        (
            "delete",
            (
                "/api/v1/identity/users/"
                "01900000-0000-7000-8000-000000000212"
                "/roles/unknown-role"
            ),
            None,
        ),
    ],
)
def test_role_routes_translate_role_not_found(
    client: TestClient,
    method: str,
    path: str,
    payload: dict[str, str] | None,
) -> None:
    from app.domain.identity.exceptions import RoleNotFound

    configure_dependencies(
        service=FakeIdentityAdministrationService(
            operation_error=RoleNotFound()
        ),
        identity=make_actor("roles.write"),
    )

    kwargs: dict[str, object] = {}

    if payload is not None:
        kwargs["json"] = payload

    response = getattr(client, method)(
        path,
        **kwargs,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == (
        "ROLE_NOT_FOUND"
    )


def test_remove_last_administrator_returns_conflict(
    client: TestClient,
) -> None:
    from app.domain.identity.exceptions import (
        CannotRemoveLastAdministrator,
    )

    configure_dependencies(
        service=FakeIdentityAdministrationService(
            operation_error=(
                CannotRemoveLastAdministrator()
            )
        ),
        identity=make_actor("roles.write"),
    )

    response = client.delete(
        (
            "/api/v1/identity/users/"
            "01900000-0000-7000-8000-000000000213"
            "/roles/administrator"
        )
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        "CANNOT_REMOVE_LAST_ADMINISTRATOR"
    )


def test_list_roles_requires_roles_read(
    client: TestClient,
) -> None:
    configure_dependencies(
        service=FakeIdentityAdministrationService(),
        identity=make_actor("roles.write"),
    )

    response = client.get(
        "/api/v1/identity/roles"
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "PERMISSION_DENIED"
    )


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "payload",
    ),
    [
        (
            "post",
            (
                "/api/v1/identity/users/"
                "01900000-0000-7000-8000-000000000214"
                "/roles"
            ),
            {"role_name": "viewer"},
        ),
        (
            "delete",
            (
                "/api/v1/identity/users/"
                "01900000-0000-7000-8000-000000000214"
                "/roles/viewer"
            ),
            None,
        ),
    ],
)
def test_role_write_routes_require_roles_write(
    client: TestClient,
    method: str,
    path: str,
    payload: dict[str, str] | None,
) -> None:
    configure_dependencies(
        service=FakeIdentityAdministrationService(),
        identity=make_actor("roles.read"),
    )

    kwargs: dict[str, object] = {}

    if payload is not None:
        kwargs["json"] = payload

    response = getattr(client, method)(
        path,
        **kwargs,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "PERMISSION_DENIED"
    )


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "payload",
    ),
    [
        (
            "get",
            "/api/v1/identity/roles",
            None,
        ),
        (
            "post",
            (
                "/api/v1/identity/users/"
                "01900000-0000-7000-8000-000000000215"
                "/roles"
            ),
            {"role_name": "operator"},
        ),
        (
            "delete",
            (
                "/api/v1/identity/users/"
                "01900000-0000-7000-8000-000000000215"
                "/roles/operator"
            ),
            None,
        ),
    ],
)
def test_role_routes_require_authentication(
    client: TestClient,
    method: str,
    path: str,
    payload: dict[str, str] | None,
) -> None:
    kwargs: dict[str, object] = {}

    if payload is not None:
        kwargs["json"] = payload

    response = getattr(client, method)(
        path,
        **kwargs,
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == (
        "Bearer"
    )


def test_role_routes_are_protected_in_openapi(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    paths = response.json()["paths"]

    operations = (
        paths[
            "/api/v1/identity/roles"
        ]["get"],
        paths[
            "/api/v1/identity/users/{user_id}/roles"
        ]["post"],
        paths[
            (
                "/api/v1/identity/users/{user_id}"
                "/roles/{role_name}"
            )
        ]["delete"],
    )

    for operation in operations:
        assert operation["security"] == [
            {
                "BearerAuth": [],
            }
        ]


def test_list_permissions_returns_canonical_permissions(
    client: TestClient,
) -> None:
    configure_dependencies(
        service=FakeIdentityAdministrationService(),
        identity=make_actor("roles.read"),
    )

    response = client.get(
        "/api/v1/identity/permissions"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["total"] == 3
    assert [
        permission["name"]
        for permission in payload["data"]["permissions"]
    ] == [
        "alarms.read",
        "dashboard.read",
        "roles.read",
    ]
    assert payload["message"] == (
        "Permisos obtenidos correctamente."
    )


def test_list_permissions_requires_roles_read(
    client: TestClient,
) -> None:
    configure_dependencies(
        service=FakeIdentityAdministrationService(),
        identity=make_actor("roles.write"),
    )

    response = client.get(
        "/api/v1/identity/permissions"
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "PERMISSION_DENIED"
    )


def test_list_permissions_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/identity/permissions"
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == (
        "Bearer"
    )


def test_permissions_route_is_protected_in_openapi(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    operation = response.json()["paths"][
        "/api/v1/identity/permissions"
    ]["get"]

    assert operation["security"] == [
        {
            "BearerAuth": [],
        }
    ]
    assert "Identity Administration" in (
        operation["tags"]
    )


@pytest.mark.parametrize(
    "status",
    [
        "disabled",
        "locked",
    ],
)
def test_last_active_administrator_status_change_returns_conflict(
    client: TestClient,
    status: str,
) -> None:
    from app.domain.identity.exceptions import (
        CannotDisableLastAdministrator,
    )

    configure_dependencies(
        service=FakeIdentityAdministrationService(
            operation_error=(
                CannotDisableLastAdministrator()
            )
        ),
        identity=make_actor("users.manage"),
    )

    response = client.patch(
        (
            "/api/v1/identity/users/"
            "01900000-0000-7000-8000-000000000401"
            "/status"
        ),
        json={
            "status": status,
        },
    )

    assert response.status_code == 409

    payload = response.json()

    assert payload["success"] is False
    assert payload["error"]["code"] == (
        "CANNOT_DISABLE_LAST_ADMINISTRATOR"
    )
