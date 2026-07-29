from dataclasses import FrozenInstanceError

import pytest

from app.domain.identity.value_objects import Email


def test_email_accepts_valid_value() -> None:
    email = Email("gerardo@example.com")

    assert email.value == "gerardo@example.com"


def test_email_strips_surrounding_whitespace() -> None:
    email = Email("  gerardo@example.com  ")

    assert email.value == "gerardo@example.com"


def test_email_preserves_letter_case() -> None:
    email = Email("Gerardo.Araya@Example.COM")

    assert email.value == "Gerardo.Araya@Example.COM"


def test_email_accepts_maximum_length() -> None:
    local_part = "a" * 242
    raw_value = f"{local_part}@example.com"

    assert len(raw_value) == Email.MAX_LENGTH
    assert Email(raw_value).value == raw_value


def test_email_rejects_non_string_value() -> None:
    with pytest.raises(TypeError, match="Email value must be a string"):
        Email(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw_value",
    [
        "",
        " ",
        "   ",
    ],
)
def test_email_rejects_empty_value(raw_value: str) -> None:
    with pytest.raises(
        ValueError,
        match="Email value must not be empty",
    ):
        Email(raw_value)


def test_email_rejects_value_longer_than_maximum() -> None:
    local_part = "a" * 243
    raw_value = f"{local_part}@example.com"

    assert len(raw_value) == Email.MAX_LENGTH + 1

    with pytest.raises(
        ValueError,
        match="Email must contain at most 254 characters",
    ):
        Email(raw_value)


@pytest.mark.parametrize(
    "raw_value",
    [
        "gerardo araya@example.com",
        "gerardo@example .com",
        "gerardo\t@example.com",
        "gerardo@\nexample.com",
    ],
)
def test_email_rejects_internal_whitespace(raw_value: str) -> None:
    with pytest.raises(
        ValueError,
        match="Email must not contain whitespace",
    ):
        Email(raw_value)


@pytest.mark.parametrize(
    "raw_value",
    [
        "gerardo\x00@example.com",
        "gerardo\x1b@example.com",
        "gerardo@example.com\x7f",
    ],
)
def test_email_rejects_control_characters(raw_value: str) -> None:
    with pytest.raises(
        ValueError,
        match="Email must not contain control characters",
    ):
        Email(raw_value)


@pytest.mark.parametrize(
    "raw_value",
    [
        "gerardo.example.com",
        "gerardo@@example.com",
        "gerardo@example@com",
    ],
)
def test_email_requires_exactly_one_at_character(raw_value: str) -> None:
    with pytest.raises(
        ValueError,
        match="Email must contain exactly one @ character",
    ):
        Email(raw_value)


def test_email_rejects_empty_local_part() -> None:
    with pytest.raises(
        ValueError,
        match="Email local part must not be empty",
    ):
        Email("@example.com")


def test_email_rejects_empty_domain() -> None:
    with pytest.raises(
        ValueError,
        match="Email domain must not be empty",
    ):
        Email("gerardo@")


def test_email_requires_dot_in_domain() -> None:
    with pytest.raises(
        ValueError,
        match="Email domain must contain at least one dot",
    ):
        Email("gerardo@localhost")


@pytest.mark.parametrize(
    "raw_value",
    [
        "gerardo@.example.com",
        "gerardo@example.com.",
    ],
)
def test_email_rejects_invalid_domain_dot_placement(
    raw_value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="Email domain dot placement is invalid",
    ):
        Email(raw_value)


def test_email_equality_is_based_on_value() -> None:
    assert Email("gerardo@example.com") == Email("gerardo@example.com")


def test_email_case_is_significant_for_equality() -> None:
    assert Email("Gerardo@example.com") != Email("gerardo@example.com")


def test_email_is_hashable() -> None:
    email = Email("gerardo@example.com")

    assert {email} == {Email("gerardo@example.com")}


def test_email_is_immutable() -> None:
    email = Email("gerardo@example.com")

    with pytest.raises(FrozenInstanceError):
        email.value = "other@example.com"  # type: ignore[misc]


def test_email_string_representation_returns_value() -> None:
    email = Email("gerardo@example.com")

    assert str(email) == "gerardo@example.com"
