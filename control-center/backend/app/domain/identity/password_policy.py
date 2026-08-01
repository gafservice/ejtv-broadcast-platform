"""Canonical password security policy for Identity."""

from __future__ import annotations

from app.domain.identity.exceptions import WeakPassword


class PasswordPolicy:
    """Validate plain-text passwords before hashing."""

    MIN_LENGTH = 12
    MAX_UTF8_BYTES = 72

    @classmethod
    def validate(cls, password: str) -> None:
        """Raise WeakPassword when a password violates the policy."""

        if not isinstance(password, str):
            raise TypeError("password must be a string")

        if password != password.strip():
            raise WeakPassword(
                "password must not contain surrounding whitespace"
            )

        if len(password) < cls.MIN_LENGTH:
            raise WeakPassword(
                f"password must contain at least "
                f"{cls.MIN_LENGTH} characters"
            )

        if len(password.encode("utf-8")) > cls.MAX_UTF8_BYTES:
            raise WeakPassword(
                f"password must not exceed "
                f"{cls.MAX_UTF8_BYTES} UTF-8 bytes"
            )

        if not any(character.isupper() for character in password):
            raise WeakPassword(
                "password must contain an uppercase letter"
            )

        if not any(character.islower() for character in password):
            raise WeakPassword(
                "password must contain a lowercase letter"
            )

        if not any(character.isdigit() for character in password):
            raise WeakPassword(
                "password must contain a number"
            )

        if not any(
            not character.isalnum()
            and not character.isspace()
            for character in password
        ):
            raise WeakPassword(
                "password must contain a special character"
            )
