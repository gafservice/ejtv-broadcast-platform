"""Tests for the TokenProvider domain protocol."""

from __future__ import annotations

from uuid import UUID

from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.protocols import TokenProvider
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)


class FakeTokenProvider:
    """Minimal structural implementation used to validate the protocol."""

    def __init__(self) -> None:
        self._tokens: dict[str, AuthenticatedIdentity] = {}

    def issue(self, identity: AuthenticatedIdentity) -> str:
        token = f"token::{identity.user_id}"
        self._tokens[token] = identity
        return token

    def verify(self, token: str) -> AuthenticatedIdentity | None:
        return self._tokens.get(token)


class IncompleteTokenProvider:
    """Object that intentionally does not satisfy the protocol."""

    def issue(self, identity: AuthenticatedIdentity) -> str:
        return "token"


def make_identity() -> AuthenticatedIdentity:
    """Build a representative authenticated identity."""

    return AuthenticatedIdentity(
        user_id=UserId(UUID("00000000-0000-0000-0000-000000000001")),
        username=Username("administrator"),
        roles=frozenset(
            {
                RoleName("administrator"),
            }
        ),
        permissions=frozenset(
            {
                PermissionName("dashboard.read"),
            }
        ),
    )


def test_complete_structural_implementation_satisfies_protocol() -> None:
    provider = FakeTokenProvider()

    assert isinstance(provider, TokenProvider)


def test_incomplete_implementation_does_not_satisfy_protocol() -> None:
    provider = IncompleteTokenProvider()

    assert not isinstance(provider, TokenProvider)


def test_protocol_exposes_issue_operation() -> None:
    assert callable(getattr(TokenProvider, "issue"))


def test_protocol_exposes_verify_operation() -> None:
    assert callable(getattr(TokenProvider, "verify"))


def test_protocol_does_not_expose_specific_token_format() -> None:
    assert not hasattr(TokenProvider, "encode_jwt")
    assert not hasattr(TokenProvider, "decode_jwt")
    assert not hasattr(TokenProvider, "refresh_jwt")


def test_protocol_does_not_expose_cryptographic_configuration() -> None:
    assert not hasattr(TokenProvider, "configure_secret")
    assert not hasattr(TokenProvider, "set_algorithm")
    assert not hasattr(TokenProvider, "load_private_key")


def test_fake_provider_can_issue_and_verify_token() -> None:
    provider = FakeTokenProvider()
    identity = make_identity()

    token = provider.issue(identity)

    assert provider.verify(token) == identity


def test_fake_provider_rejects_unknown_token() -> None:
    provider = FakeTokenProvider()

    assert provider.verify("unknown-token") is None


def test_issued_token_is_an_opaque_string() -> None:
    provider = FakeTokenProvider()

    token = provider.issue(make_identity())

    assert isinstance(token, str)
    assert token
