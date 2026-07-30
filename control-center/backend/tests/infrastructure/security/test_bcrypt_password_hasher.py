"""Tests for the bcrypt password hasher infrastructure adapter."""

from __future__ import annotations

import pytest

from app.domain.identity.protocols import PasswordHasher
from app.domain.identity.value_objects import PasswordHash
from app.infrastructure.security import BcryptPasswordHasher


PLAIN_PASSWORD = "Correct-Horse-Battery-Staple-2026!"


def test_implements_password_hasher_protocol() -> None:
    hasher = BcryptPasswordHasher(rounds=4)

    assert isinstance(hasher, PasswordHasher)


def test_hash_returns_password_hash() -> None:
    hasher = BcryptPasswordHasher(rounds=4)

    result = hasher.hash(PLAIN_PASSWORD)

    assert isinstance(result, PasswordHash)
    assert result.value.startswith(("$2a$", "$2b$", "$2y$"))
    assert PLAIN_PASSWORD not in result.value


def test_hash_uses_a_random_salt() -> None:
    hasher = BcryptPasswordHasher(rounds=4)

    first_hash = hasher.hash(PLAIN_PASSWORD)
    second_hash = hasher.hash(PLAIN_PASSWORD)

    assert first_hash != second_hash


def test_verify_accepts_matching_password() -> None:
    hasher = BcryptPasswordHasher(rounds=4)
    password_hash = hasher.hash(PLAIN_PASSWORD)

    assert hasher.verify(PLAIN_PASSWORD, password_hash) is True


def test_verify_rejects_non_matching_password() -> None:
    hasher = BcryptPasswordHasher(rounds=4)
    password_hash = hasher.hash(PLAIN_PASSWORD)

    assert hasher.verify("Wrong-password-2026!", password_hash) is False


def test_verify_rejects_malformed_hash() -> None:
    hasher = BcryptPasswordHasher(rounds=4)
    malformed_hash = PasswordHash("not-a-valid-bcrypt-hash")

    assert hasher.verify(PLAIN_PASSWORD, malformed_hash) is False


@pytest.mark.parametrize(
    "plain_password",
    [
        "",
        "a" * 73,
        "á" * 37,
    ],
)
def test_hash_rejects_invalid_password(
    plain_password: str,
) -> None:
    hasher = BcryptPasswordHasher(rounds=4)

    with pytest.raises(ValueError):
        hasher.hash(plain_password)


@pytest.mark.parametrize("plain_password", [None, 123, b"password"])
def test_hash_rejects_non_string_password(
    plain_password: object,
) -> None:
    hasher = BcryptPasswordHasher(rounds=4)

    with pytest.raises(TypeError):
        hasher.hash(plain_password)  # type: ignore[arg-type]


@pytest.mark.parametrize("rounds", [3, 32, -1])
def test_rejects_rounds_outside_bcrypt_range(rounds: int) -> None:
    with pytest.raises(ValueError):
        BcryptPasswordHasher(rounds=rounds)


@pytest.mark.parametrize("rounds", [True, 12.0, "12", None])
def test_rejects_non_integer_rounds(rounds: object) -> None:
    with pytest.raises(TypeError):
        BcryptPasswordHasher(rounds=rounds)  # type: ignore[arg-type]


def test_exposes_configured_rounds() -> None:
    hasher = BcryptPasswordHasher(rounds=6)

    assert hasher.rounds == 6
