"""Tests for the canonical Identity password policy."""

import pytest

from app.domain.identity.exceptions import WeakPassword
from app.domain.identity.password_policy import PasswordPolicy


def test_accepts_strong_password() -> None:
    PasswordPolicy.validate("Secure-Password-2026!")


@pytest.mark.parametrize(
    "password",
    [
        "Short1!",
        "lowercase-only-2026!",
        "UPPERCASE-ONLY-2026!",
        "NoNumbersHere!",
        "NoSpecialCharacter2026",
        " Leading-Secure-2026!",
        "Trailing-Secure-2026! ",
    ],
)
def test_rejects_password_policy_violations(
    password: str,
) -> None:
    with pytest.raises(WeakPassword):
        PasswordPolicy.validate(password)


def test_rejects_password_over_72_utf8_bytes() -> None:
    password = "Á" * 35 + "Aa1!"

    assert len(password) < 72
    assert len(password.encode("utf-8")) > 72

    with pytest.raises(WeakPassword):
        PasswordPolicy.validate(password)


def test_rejects_non_string_password() -> None:
    with pytest.raises(
        TypeError,
        match="password must be a string",
    ):
        PasswordPolicy.validate(
            123456  # type: ignore[arg-type]
        )
