from dataclasses import FrozenInstanceError

import pytest

from app.domain.identity.value_objects import PasswordHash


ARGON2_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "c29tZXNhbHQ$"
    "bG9uZ2VuY29kZWRoYXNodmFsdWU"
)

BCRYPT_HASH = (
    "$2b$12$"
    "abcdefghijklmnopqrstuu"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
)


def test_password_hash_accepts_argon2_encoded_hash() -> None:
    password_hash = PasswordHash(ARGON2_HASH)

    assert password_hash.value == ARGON2_HASH


def test_password_hash_accepts_bcrypt_encoded_hash() -> None:
    password_hash = PasswordHash(BCRYPT_HASH)

    assert password_hash.value == BCRYPT_HASH


def test_password_hash_strips_surrounding_whitespace() -> None:
    password_hash = PasswordHash(
        f"  {ARGON2_HASH}\n"
    )

    assert password_hash.value == ARGON2_HASH


@pytest.mark.parametrize(
    "invalid_value",
    [
        "",
        " ",
        "\n",
        "\t",
    ],
)
def test_password_hash_rejects_empty_value(
    invalid_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        PasswordHash(invalid_value)


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        123,
        b"encoded-hash",
        [],
    ],
)
def test_password_hash_rejects_non_string_value(
    invalid_value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        PasswordHash(invalid_value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "invalid_value",
    [
        "$argon2id$invalid hash",
        "$2b$12$invalid\thash",
        "$encoded\nhash",
    ],
)
def test_password_hash_rejects_internal_whitespace(
    invalid_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not contain whitespace",
    ):
        PasswordHash(invalid_value)


def test_password_hash_rejects_excessive_length() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 1024 characters",
    ):
        PasswordHash("x" * 1025)


def test_password_hash_accepts_maximum_length() -> None:
    value = "x" * PasswordHash.MAX_LENGTH

    password_hash = PasswordHash(value)

    assert password_hash.value == value


def test_password_hash_is_immutable() -> None:
    password_hash = PasswordHash(ARGON2_HASH)

    with pytest.raises(FrozenInstanceError):
        password_hash.value = BCRYPT_HASH  # type: ignore[misc]


def test_password_hash_equality_is_based_on_value() -> None:
    left = PasswordHash(ARGON2_HASH)
    right = PasswordHash(ARGON2_HASH)

    assert left == right


def test_different_password_hashes_are_not_equal() -> None:
    left = PasswordHash(ARGON2_HASH)
    right = PasswordHash(BCRYPT_HASH)

    assert left != right


def test_password_hash_is_hashable() -> None:
    password_hashes = {
        PasswordHash(ARGON2_HASH),
    }

    assert PasswordHash(ARGON2_HASH) in password_hashes


def test_password_hash_repr_does_not_expose_value() -> None:
    password_hash = PasswordHash(ARGON2_HASH)

    representation = repr(password_hash)

    assert ARGON2_HASH not in representation
