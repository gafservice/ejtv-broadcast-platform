from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from app.domain.identity.value_objects import UserId


def test_user_id_accepts_uuid_value() -> None:
    value = UUID("12345678-1234-5678-1234-567812345678")

    user_id = UserId(value)

    assert user_id.value == value


def test_user_id_rejects_non_uuid_value() -> None:
    with pytest.raises(TypeError, match="UserId value must be a UUID"):
        UserId("12345678-1234-5678-1234-567812345678")  # type: ignore[arg-type]


def test_user_id_generate_creates_valid_uuid() -> None:
    user_id = UserId.generate()

    assert isinstance(user_id.value, UUID)


def test_user_id_generate_creates_unique_values() -> None:
    first = UserId.generate()
    second = UserId.generate()

    assert first != second


def test_user_id_can_be_reconstructed_from_string() -> None:
    raw_value = "12345678-1234-5678-1234-567812345678"

    user_id = UserId.from_string(raw_value)

    assert user_id.value == UUID(raw_value)


def test_user_id_from_string_rejects_invalid_uuid() -> None:
    with pytest.raises(ValueError, match="Invalid UserId value"):
        UserId.from_string("not-a-uuid")


def test_user_id_from_string_rejects_non_string_value() -> None:
    with pytest.raises(
        TypeError,
        match="UserId string value must be a string",
    ):
        UserId.from_string(123)  # type: ignore[arg-type]


def test_user_id_equality_is_based_on_value() -> None:
    value = UUID("12345678-1234-5678-1234-567812345678")

    assert UserId(value) == UserId(value)


def test_user_id_is_hashable() -> None:
    value = UUID("12345678-1234-5678-1234-567812345678")
    user_id = UserId(value)

    assert {user_id} == {UserId(value)}


def test_user_id_is_immutable() -> None:
    user_id = UserId.generate()

    with pytest.raises(FrozenInstanceError):
        user_id.value = UUID("12345678-1234-5678-1234-567812345678")  # type: ignore[misc]


def test_user_id_string_representation_returns_uuid() -> None:
    raw_value = "12345678-1234-5678-1234-567812345678"

    user_id = UserId.from_string(raw_value)

    assert str(user_id) == raw_value
