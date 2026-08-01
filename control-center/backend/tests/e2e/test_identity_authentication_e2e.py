"""End-to-end authentication tests for Identity."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.identity.catalog import ALL_PERMISSIONS
from app.infrastructure.persistence.audit.models import (
    AuditLogModel,
)


def test_administrator_login_and_current_identity(
    e2e_client: TestClient,
    administrator_credentials: dict[str, str],
) -> None:
    """Authenticate through HTTP and consume the issued JWT."""

    login_response = e2e_client.post(
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

    assert login_response.status_code == 200

    login_payload = login_response.json()

    assert login_payload["success"] is True
    assert login_payload["data"]["token_type"] == "Bearer"
    assert login_payload["data"]["expires_in"] == 900

    access_token = login_payload["data"]["access_token"]

    assert isinstance(access_token, str)
    assert access_token.count(".") == 2

    current_identity_response = e2e_client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert current_identity_response.status_code == 200

    identity_payload = current_identity_response.json()

    assert identity_payload["success"] is True

    identity = identity_payload["data"]

    assert identity["username"] == (
        administrator_credentials["username"]
    )
    assert identity["roles"] == [
        "administrator",
    ]
    assert set(identity["permissions"]) == {
        permission.value
        for permission in ALL_PERMISSIONS
    }
    assert identity["user_id"]


def test_successful_login_is_persisted_in_audit_log(
    administrator_token: str,
    identity_session_factory: sessionmaker[Session],
    administrator_credentials: dict[str, str],
) -> None:
    """Confirm that a real login produces a database audit event."""

    assert administrator_token

    with identity_session_factory() as session:
        audit_events = tuple(
            session.scalars(
                select(AuditLogModel)
                .where(
                    AuditLogModel.event_type
                    == "identity.login.succeeded"
                )
                .order_by(AuditLogModel.id)
            )
        )

    assert audit_events

    event = audit_events[-1]

    assert event.username == (
        administrator_credentials["username"]
    )
    assert event.user_id
    assert json.loads(event.roles_json) == [
        "administrator",
    ]

    persisted_permissions = set(
        json.loads(event.permissions_json)
    )

    assert persisted_permissions == {
        permission.value
        for permission in ALL_PERMISSIONS
    }

    assert json.loads(event.details_json) == {
        "username": (
            administrator_credentials["username"]
        )
    }


def test_current_identity_rejects_missing_token(
    e2e_client: TestClient,
) -> None:
    """Reject access when no Bearer token is supplied."""

    response = e2e_client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == (
        "Bearer"
    )


def test_current_identity_rejects_invalid_token(
    e2e_client: TestClient,
) -> None:
    """Reject an invalid signed-token representation."""

    response = e2e_client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                "Bearer invalid.header.signature"
            ),
        },
    )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == (
        "Bearer"
    )
