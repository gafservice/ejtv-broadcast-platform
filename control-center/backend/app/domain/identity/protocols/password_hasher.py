"""Domain contract for password hashing."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.identity.value_objects import PasswordHash


@runtime_checkable
class PasswordHasher(Protocol):
    """Contract for hashing and verifying user passwords.

    Cryptographic algorithms and external libraries belong to the
    infrastructure layer. The domain depends only on this abstraction.
    """

    def hash(self, plain_password: str) -> PasswordHash:
        """Create a secure hash from a plain-text password."""
        ...

    def verify(
        self,
        plain_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        """Return whether the plain-text password matches the stored hash."""
        ...
