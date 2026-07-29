"""Tests for the PasswordHasher domain protocol."""

from __future__ import annotations

from app.domain.identity.protocols import PasswordHasher
from app.domain.identity.value_objects import PasswordHash


class FakePasswordHasher:
    """Minimal structural implementation used to validate the protocol."""

    def hash(self, plain_password: str) -> PasswordHash:
        return PasswordHash(f"hashed::{plain_password}")

    def verify(
        self,
        plain_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        return password_hash == PasswordHash(f"hashed::{plain_password}")


class IncompletePasswordHasher:
    """Object that intentionally does not satisfy the protocol."""

    def hash(self, plain_password: str) -> PasswordHash:
        return PasswordHash(f"hashed::{plain_password}")


def test_complete_structural_implementation_satisfies_protocol() -> None:
    hasher = FakePasswordHasher()

    assert isinstance(hasher, PasswordHasher)


def test_incomplete_implementation_does_not_satisfy_protocol() -> None:
    hasher = IncompletePasswordHasher()

    assert not isinstance(hasher, PasswordHasher)


def test_protocol_exposes_hash_operation() -> None:
    assert callable(getattr(PasswordHasher, "hash"))


def test_protocol_exposes_verify_operation() -> None:
    assert callable(getattr(PasswordHasher, "verify"))


def test_protocol_does_not_expose_specific_algorithm_operations() -> None:
    assert not hasattr(PasswordHasher, "argon2")
    assert not hasattr(PasswordHasher, "bcrypt")
    assert not hasattr(PasswordHasher, "scrypt")


def test_protocol_does_not_expose_infrastructure_configuration() -> None:
    assert not hasattr(PasswordHasher, "configure")
    assert not hasattr(PasswordHasher, "connect")
    assert not hasattr(PasswordHasher, "initialize")


def test_fake_hasher_can_hash_and_verify_password() -> None:
    hasher = FakePasswordHasher()

    password_hash = hasher.hash("correct-password")

    assert hasher.verify("correct-password", password_hash)


def test_fake_hasher_rejects_incorrect_password() -> None:
    hasher = FakePasswordHasher()

    password_hash = hasher.hash("correct-password")

    assert not hasher.verify("incorrect-password", password_hash)
