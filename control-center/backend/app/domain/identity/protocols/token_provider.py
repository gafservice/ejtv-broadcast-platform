"""Domain contract for authentication tokens."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.identity.entities import AuthenticatedIdentity


@runtime_checkable
class TokenProvider(Protocol):
    """Contract for issuing and validating authentication tokens.

    Token formats, cryptographic algorithms, secret keys, expiration rules
    and external libraries belong to the infrastructure layer.
    """

    def issue(self, identity: AuthenticatedIdentity) -> str:
        """Issue a token representing the authenticated identity."""
        ...

    def verify(self, token: str) -> AuthenticatedIdentity | None:
        """Return the authenticated identity represented by a valid token."""
        ...
