"""Shared infrastructure for real end-to-end tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


ADMINISTRATOR_USERNAME = "administrator"
ADMINISTRATOR_EMAIL = "administrator.e2e@example.com"
ADMINISTRATOR_PASSWORD = "Administrator-E2E-2026!"

JWT_SECRET_KEY = (
    "e2e-test-secret-key-with-more-than-thirty-two-bytes"
)


def _clear_dependency_caches() -> None:
    """Clear cached Identity dependencies."""

    from app.api import dependencies

    dependency_names = (
        "get_identity_database_engine",
        "get_identity_session_factory",
        "get_token_provider",
        "get_audit_repository",
        "get_authorization_service",
        "get_identity_administration_service",
        "get_authentication_service",
    )

    for dependency_name in dependency_names:
        dependency = getattr(
            dependencies,
            dependency_name,
            None,
        )

        cache_clear = getattr(
            dependency,
            "cache_clear",
            None,
        )

        if callable(cache_clear):
            cache_clear()


def _dispose_cached_identity_engine() -> None:
    """Dispose the cached Identity database engine."""

    from app.api.dependencies import (
        get_identity_database_engine,
    )

    if (
        get_identity_database_engine.cache_info().currsize
        == 0
    ):
        return

    engine = get_identity_database_engine()

    if isinstance(engine, Engine):
        engine.dispose()


@pytest.fixture
def administrator_credentials() -> dict[str, str]:
    """Return the E2E administrator credentials."""

    return {
        "username": ADMINISTRATOR_USERNAME,
        "email": ADMINISTRATOR_EMAIL,
        "password": ADMINISTRATOR_PASSWORD,
    }


@pytest.fixture
def e2e_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Settings]:
    """Configure an isolated Identity environment."""

    database_path = tmp_path / "identity-e2e.db"
    database_url = (
        f"sqlite+pysqlite:///{database_path}"
    )

    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv(
        "IDENTITY_DATABASE_URL",
        database_url,
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        JWT_SECRET_KEY,
    )
    monkeypatch.setenv(
        "JWT_ISSUER",
        "control-center-e2e",
    )
    monkeypatch.setenv(
        "JWT_AUDIENCE",
        "control-center-e2e-api",
    )
    monkeypatch.setenv(
        "JWT_EXPIRATION_SECONDS",
        "900",
    )
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")
    monkeypatch.setenv(
        "BOOTSTRAP_ADMIN_USERNAME",
        ADMINISTRATOR_USERNAME,
    )
    monkeypatch.setenv(
        "BOOTSTRAP_ADMIN_EMAIL",
        ADMINISTRATOR_EMAIL,
    )
    monkeypatch.setenv(
        "BOOTSTRAP_ADMIN_PASSWORD",
        ADMINISTRATOR_PASSWORD,
    )

    from app.core.config import get_settings

    get_settings.cache_clear()
    _clear_dependency_caches()

    settings = get_settings()

    assert settings.environment == "testing"
    assert settings.identity_database_url == database_url

    try:
        yield settings
    finally:
        _dispose_cached_identity_engine()
        _clear_dependency_caches()
        get_settings.cache_clear()


@pytest.fixture
def e2e_application(
    e2e_settings: Settings,
) -> Iterator[FastAPI]:
    """Create a FastAPI application for the E2E database."""

    import app.main as main_module

    main_module.settings = e2e_settings

    application = main_module.create_application()

    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture
def e2e_client(
    e2e_application: FastAPI,
    e2e_settings: Settings,
    administrator_credentials: dict[str, str],
) -> Iterator[TestClient]:
    """Start FastAPI and create the bootstrap administrator."""

    from app.identity.bootstrap_admin import (
        build_bootstrap_service,
    )
    from app.services.identity_bootstrap_service import (
        BootstrapStatus,
    )

    with TestClient(e2e_application) as client:
        bootstrap_service = build_bootstrap_service(
            e2e_settings
        )

        catalog_result = (
            bootstrap_service.synchronize_catalog()
        )

        assert catalog_result.total == 3

        integrity_result = (
            bootstrap_service.verify_integrity()
        )

        assert integrity_result.valid is True

        bootstrap_result = (
            bootstrap_service.bootstrap_administrator(
                username=(
                    administrator_credentials["username"]
                ),
                email=administrator_credentials["email"],
                password=(
                    administrator_credentials["password"]
                ),
            )
        )

        assert bootstrap_result.status in (
            BootstrapStatus.CREATED,
            BootstrapStatus.ALREADY_EXISTS,
        )

        yield client


@pytest.fixture
def identity_session_factory(
    e2e_client: TestClient,
) -> sessionmaker[Session]:
    """Return the session factory used by the API."""

    del e2e_client

    from app.api.dependencies import (
        get_identity_session_factory,
    )

    return get_identity_session_factory()


@pytest.fixture
def administrator_token(
    e2e_client: TestClient,
    administrator_credentials: dict[str, str],
) -> str:
    """Authenticate the real administrator."""

    response = e2e_client.post(
        "/api/v1/auth/login",
        json={
            "username": (
                administrator_credentials["username"]
            ),
            "password": (
                administrator_credentials["password"]
            ),
        },
    )

    assert response.status_code == 200, response.text

    payload: dict[str, Any] = response.json()

    token = payload["data"]["access_token"]

    assert isinstance(token, str)
    assert token

    return token


@pytest.fixture
def authorization_headers(
    administrator_token: str,
) -> dict[str, str]:
    """Return the administrator Bearer header."""

    return {
        "Authorization": (
            f"Bearer {administrator_token}"
        )
    }
