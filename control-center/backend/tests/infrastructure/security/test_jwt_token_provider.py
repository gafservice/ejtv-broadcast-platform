"""Tests for the JWT token-provider infrastructure adapter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest

from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.protocols import TokenProvider
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.infrastructure.security import JWTTokenProvider


SECRET_KEY = "test-secret-key-with-at-least-32-bytes"
OTHER_SECRET_KEY = "other-secret-key-with-at-least-32-bytes"
ISSUER = "broadcast-platform"
AUDIENCE = "broadcast-api"


def make_provider(
    *,
    secret_key: str = SECRET_KEY,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    expiration_seconds: int = 900,
    leeway_seconds: int = 0,
) -> JWTTokenProvider:
    return JWTTokenProvider(
        secret_key=secret_key,
        issuer=issuer,
        audience=audience,
        expiration_seconds=expiration_seconds,
        leeway_seconds=leeway_seconds,
    )


def make_identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        user_id=UserId(
            UUID("00000000-0000-0000-0000-000000000001")
        ),
        username=Username("administrator"),
        roles=frozenset(
            {
                RoleName("operator"),
                RoleName("administrator"),
            }
        ),
        permissions=frozenset(
            {
                PermissionName("streams.manage"),
                PermissionName("dashboard.read"),
            }
        ),
    )


def make_claims(
    *,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
) -> dict[str, object]:
    issued_at = datetime.now(timezone.utc)

    return {
        "sub": "00000000-0000-0000-0000-000000000001",
        "username": "administrator",
        "roles": ["administrator"],
        "permissions": ["dashboard.read"],
        "iat": issued_at,
        "nbf": issued_at,
        "exp": issued_at + timedelta(minutes=15),
        "iss": issuer,
        "aud": audience,
        "jti": "00000000-0000-0000-0000-000000000002",
    }


def encode_claims(
    claims: dict[str, object],
    *,
    secret_key: str = SECRET_KEY,
) -> str:
    return jwt.encode(
        claims,
        secret_key,
        algorithm=JWTTokenProvider.ALGORITHM,
    )


def test_implements_token_provider_protocol() -> None:
    provider = make_provider()

    assert isinstance(provider, TokenProvider)


def test_issue_returns_non_empty_token() -> None:
    provider = make_provider()

    token = provider.issue(make_identity())

    assert isinstance(token, str)
    assert token


def test_issue_and_verify_round_trip() -> None:
    provider = make_provider()
    identity = make_identity()

    token = provider.issue(identity)

    assert provider.verify(token) == identity


def test_issue_contains_expected_claims() -> None:
    provider = make_provider()
    identity = make_identity()

    token = provider.issue(identity)

    claims = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[JWTTokenProvider.ALGORITHM],
        audience=AUDIENCE,
        issuer=ISSUER,
    )

    assert claims["sub"] == str(identity.user_id)
    assert claims["username"] == identity.username.value
    assert claims["roles"] == ["administrator", "operator"]
    assert claims["permissions"] == [
        "dashboard.read",
        "streams.manage",
    ]
    assert claims["iss"] == ISSUER
    assert claims["aud"] == AUDIENCE
    assert isinstance(claims["jti"], str)
    assert claims["jti"]


def test_each_issued_token_has_unique_jti() -> None:
    provider = make_provider()
    identity = make_identity()

    first_token = provider.issue(identity)
    second_token = provider.issue(identity)

    first_claims = jwt.decode(
        first_token,
        SECRET_KEY,
        algorithms=[JWTTokenProvider.ALGORITHM],
        audience=AUDIENCE,
        issuer=ISSUER,
    )
    second_claims = jwt.decode(
        second_token,
        SECRET_KEY,
        algorithms=[JWTTokenProvider.ALGORITHM],
        audience=AUDIENCE,
        issuer=ISSUER,
    )

    assert first_claims["jti"] != second_claims["jti"]


def test_verify_rejects_token_signed_with_other_key() -> None:
    provider = make_provider()
    token = encode_claims(
        make_claims(),
        secret_key=OTHER_SECRET_KEY,
    )

    assert provider.verify(token) is None


def test_verify_rejects_wrong_issuer() -> None:
    provider = make_provider()
    token = encode_claims(
        make_claims(issuer="another-platform")
    )

    assert provider.verify(token) is None


def test_verify_rejects_wrong_audience() -> None:
    provider = make_provider()
    token = encode_claims(
        make_claims(audience="another-api")
    )

    assert provider.verify(token) is None


def test_verify_rejects_expired_token() -> None:
    provider = make_provider()
    claims = make_claims()
    claims["exp"] = datetime.now(timezone.utc) - timedelta(
        seconds=1
    )

    token = encode_claims(claims)

    assert provider.verify(token) is None


def test_verify_rejects_token_not_yet_valid() -> None:
    provider = make_provider()
    claims = make_claims()
    claims["nbf"] = datetime.now(timezone.utc) + timedelta(
        minutes=5
    )

    token = encode_claims(claims)

    assert provider.verify(token) is None


@pytest.mark.parametrize(
    "missing_claim",
    JWTTokenProvider.REQUIRED_CLAIMS,
)
def test_verify_rejects_missing_required_claim(
    missing_claim: str,
) -> None:
    provider = make_provider()
    claims = make_claims()
    del claims[missing_claim]

    token = encode_claims(claims)

    assert provider.verify(token) is None


@pytest.mark.parametrize(
    ("claim_name", "invalid_value"),
    [
        ("sub", "invalid-uuid"),
        ("username", ""),
        ("roles", "administrator"),
        ("roles", [123]),
        ("roles", ["INVALID ROLE"]),
        ("permissions", "dashboard.read"),
        ("permissions", [123]),
        ("permissions", ["invalid"]),
    ],
)
def test_verify_rejects_invalid_identity_claims(
    claim_name: str,
    invalid_value: object,
) -> None:
    provider = make_provider()
    claims = make_claims()
    claims[claim_name] = invalid_value

    token = encode_claims(claims)

    assert provider.verify(token) is None


@pytest.mark.parametrize(
    "token",
    [
        "",
        "   ",
        "not-a-jwt",
        None,
        123,
        b"token",
    ],
)
def test_verify_rejects_invalid_token_input(
    token: object,
) -> None:
    provider = make_provider()

    assert provider.verify(token) is None  # type: ignore[arg-type]


def test_issue_rejects_invalid_identity() -> None:
    provider = make_provider()

    with pytest.raises(TypeError):
        provider.issue(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "secret_key",
    [
        "",
        "short",
        "á" * 15,
    ],
)
def test_rejects_short_secret_key(secret_key: str) -> None:
    with pytest.raises(ValueError):
        make_provider(secret_key=secret_key)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("secret_key", None),
        ("issuer", None),
        ("audience", None),
    ],
)
def test_rejects_non_string_configuration(
    field_name: str,
    field_value: object,
) -> None:
    arguments: dict[str, object] = {
        "secret_key": SECRET_KEY,
        "issuer": ISSUER,
        "audience": AUDIENCE,
    }
    arguments[field_name] = field_value

    with pytest.raises(TypeError):
        JWTTokenProvider(**arguments)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("issuer", ""),
        ("issuer", "   "),
        ("audience", ""),
        ("audience", "   "),
    ],
)
def test_rejects_empty_text_configuration(
    field_name: str,
    field_value: str,
) -> None:
    arguments = {
        "secret_key": SECRET_KEY,
        "issuer": ISSUER,
        "audience": AUDIENCE,
    }
    arguments[field_name] = field_value

    with pytest.raises(ValueError):
        JWTTokenProvider(**arguments)


@pytest.mark.parametrize(
    "expiration_seconds",
    [0, -1],
)
def test_rejects_non_positive_expiration(
    expiration_seconds: int,
) -> None:
    with pytest.raises(ValueError):
        make_provider(
            expiration_seconds=expiration_seconds
        )


@pytest.mark.parametrize(
    "expiration_seconds",
    [True, 900.0, "900", None],
)
def test_rejects_non_integer_expiration(
    expiration_seconds: object,
) -> None:
    with pytest.raises(TypeError):
        make_provider(
            expiration_seconds=expiration_seconds  # type: ignore[arg-type]
        )


def test_exposes_configuration() -> None:
    provider = make_provider(
        expiration_seconds=1800,
        leeway_seconds=30,
    )

    assert provider.issuer == ISSUER
    assert provider.audience == AUDIENCE
    assert provider.expiration_seconds == 1800
    assert provider.leeway_seconds == 30
