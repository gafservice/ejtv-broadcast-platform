from dataclasses import FrozenInstanceError

import pytest

from app.domain.identity.value_objects import Username


def test_username_accepts_valid_value() -> None:
    username = Username("gerardo")

    assert username.value == "gerardo"


def test_username_strips_surrounding_whitespace() -> None:
    username = Username("  gerardo  ")

    assert username.value == "gerardo"


def test_username_preserves_letter_case() -> None:
    username = Username("Gerardo.Araya")

    assert username.value == "Gerardo.Araya"


def test_username_accepts_minimum_length() -> None:
    username = Username("abc")

    assert username.value == "abc"


def test_username_accepts_maximum_length() -> None:
    raw_value = "a" * Username.MAX_LENGTH

    username = Username(raw_value)

    assert username.value == raw_value


def test_username_rejects_non_string_value() -> None:
    with pytest.raises(TypeError, match="Username value must be a string"):
        Username(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw_value",
    [
        "",
        " ",
        "ab",
        "  ab  ",
    ],
)
def test_username_rejects_value_shorter_than_minimum(
    raw_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="Username must contain at least 3 characters",
    ):
        Username(raw_value)


def test_username_rejects_value_longer_than_maximum() -> None:
    raw_value = "a" * (Username.MAX_LENGTH + 1)

    with pytest.raises(
        ValueError,
        match="Username must contain at most 64 characters",
    ):
        Username(raw_value)


@pytest.mark.parametrize(
    "raw_value",
    [
        "user\nname",
        "user\tname",
        "user\rname",
        "user\x00name",
    ],
)
def test_username_rejects_control_characters(
    raw_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="Username must not contain control characters",
    ):
        Username(raw_value)


def test_username_equality_is_based_on_value() -> None:
    assert Username("gerardo") == Username("gerardo")


def test_username_case_is_significant_for_equality() -> None:
    assert Username("Gerardo") != Username("gerardo")


def test_username_is_hashable() -> None:
    username = Username("gerardo")

    assert {username} == {Username("gerardo")}


def test_username_is_immutable() -> None:
    username = Username("gerardo")

    with pytest.raises(FrozenInstanceError):
        username.value = "new-name"  # type: ignore[misc]


def test_username_string_representation_returns_value() -> None:
    username = Username("gerardo")

    assert str(username) == "gerardo"
