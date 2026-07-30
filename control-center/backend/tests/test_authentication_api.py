"""Pruebas de la API de autenticación."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_authentication_service
from app.domain.identity.exceptions import (
    InvalidCredentials,
    UserDisabled,
    UserLocked,
)
from app.main import app


class FakeAuthenticationService:
    """Servicio controlado para pruebas HTTP."""

    def __init__(
        self,
        *,
        token: str = "test.jwt.token",
        error: Exception | None = None,
    ) -> None:
        self.token = token
        self.error = error
        self.received_username: str | None = None
        self.received_password: str | None = None

    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> str:
        self.received_username = username
        self.received_password = password

        if self.error is not None:
            raise self.error

        return self.token


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Proporciona un cliente aislado por prueba."""

    previous_override = app.dependency_overrides.get(
        get_authentication_service
    )

    with TestClient(app) as test_client:
        yield test_client

    if previous_override is None:
        app.dependency_overrides.pop(
            get_authentication_service,
            None,
        )
    else:
        app.dependency_overrides[
            get_authentication_service
        ] = previous_override


def override_authentication_service(
    service: FakeAuthenticationService,
) -> None:
    app.dependency_overrides[
        get_authentication_service
    ] = lambda: service


def test_login_returns_access_token(
    client: TestClient,
) -> None:
    service = FakeAuthenticationService(
        token="header.payload.signature"
    )
    override_authentication_service(service)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "administrator",
            "password": "secure-password",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert payload["data"]["access_token"] == (
        "header.payload.signature"
    )
    assert payload["data"]["token_type"] == "Bearer"
    assert payload["data"]["expires_in"] == 900
    assert payload["message"] == (
        "Autenticación completada correctamente."
    )
    assert payload["request_id"]
    assert payload["timestamp"]

    assert service.received_username == "administrator"
    assert service.received_password == "secure-password"


def test_login_preserves_request_id(
    client: TestClient,
) -> None:
    service = FakeAuthenticationService()
    override_authentication_service(service)

    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Request-ID": "authentication-test"},
        json={
            "username": "administrator",
            "password": "secure-password",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == (
        "authentication-test"
    )
    assert response.json()["request_id"] == (
        "authentication-test"
    )


def test_login_rejects_invalid_credentials(
    client: TestClient,
) -> None:
    service = FakeAuthenticationService(
        error=InvalidCredentials()
    )
    override_authentication_service(service)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "administrator",
            "password": "incorrect-password",
        },
    )

    assert response.status_code == 401

    payload = response.json()

    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"]["code"] == (
        "INVALID_CREDENTIALS"
    )
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_login_rejects_disabled_user(
    client: TestClient,
) -> None:
    service = FakeAuthenticationService(
        error=UserDisabled()
    )
    override_authentication_service(service)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "administrator",
            "password": "secure-password",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == (
        "USER_DISABLED"
    )


def test_login_rejects_locked_user(
    client: TestClient,
) -> None:
    service = FakeAuthenticationService(
        error=UserLocked()
    )
    override_authentication_service(service)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "administrator",
            "password": "secure-password",
        },
    )

    assert response.status_code == 423
    assert response.json()["error"]["code"] == (
        "USER_LOCKED"
    )


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        (
            {
                "username": "ab",
                "password": "secure-password",
            },
            "username",
        ),
        (
            {
                "username": "administrator",
                "password": "",
            },
            "password",
        ),
    ],
)
def test_login_validates_request_body(
    client: TestClient,
    payload: dict[str, str],
    field: str,
) -> None:
    service = FakeAuthenticationService()
    override_authentication_service(service)

    response = client.post(
        "/api/v1/auth/login",
        json=payload,
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert any(
        error["loc"][-1] == field
        for error in body["error"]["details"]
    )


def test_login_is_registered_in_openapi(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    operation = response.json()["paths"][
        "/api/v1/auth/login"
    ]["post"]

    assert "Authentication" in operation["tags"]
