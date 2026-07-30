"""bcrypt implementation of the password-hashing domain contract."""

from __future__ import annotations

import bcrypt

from app.domain.identity.value_objects import PasswordHash


class BcryptPasswordHasher:
    """Hash and verify passwords using the bcrypt algorithm.

    This implementation belongs to the infrastructure layer. The domain
    and application layers depend only on the PasswordHasher protocol.
    """

    DEFAULT_ROUNDS = 12
    MIN_ROUNDS = 4
    MAX_ROUNDS = 31
    MAX_PASSWORD_BYTES = 72

    def __init__(self, rounds: int = DEFAULT_ROUNDS) -> None:
        if isinstance(rounds, bool) or not isinstance(rounds, int):
            raise TypeError("bcrypt rounds must be an integer")

        if not self.MIN_ROUNDS <= rounds <= self.MAX_ROUNDS:
            raise ValueError(
                "bcrypt rounds must be between "
                f"{self.MIN_ROUNDS} and {self.MAX_ROUNDS}"
            )

        self._rounds = rounds

    @property
    def rounds(self) -> int:
        """Return the configured bcrypt cost factor."""
        return self._rounds

    def hash(self, plain_password: str) -> PasswordHash:
        """Create a bcrypt hash from a plain-text password."""
        password_bytes = self._encode_password(plain_password)

        encoded_hash = bcrypt.hashpw(
            password_bytes,
            bcrypt.gensalt(rounds=self._rounds),
        )

        return PasswordHash(encoded_hash.decode("ascii"))

    def verify(
        self,
        plain_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        """Return whether a password matches an encoded bcrypt hash."""
        if not isinstance(password_hash, PasswordHash):
            raise TypeError("password_hash must be a PasswordHash")

        try:
            password_bytes = self._encode_password(plain_password)
            encoded_hash = password_hash.value.encode("ascii")

            return bcrypt.checkpw(password_bytes, encoded_hash)
        except (UnicodeEncodeError, ValueError):
            return False

    @classmethod
    def _encode_password(cls, plain_password: str) -> bytes:
        if not isinstance(plain_password, str):
            raise TypeError("plain password must be a string")

        if not plain_password:
            raise ValueError("plain password must not be empty")

        password_bytes = plain_password.encode("utf-8")

        if len(password_bytes) > cls.MAX_PASSWORD_BYTES:
            raise ValueError(
                "plain password must not exceed "
                f"{cls.MAX_PASSWORD_BYTES} UTF-8 bytes"
            )

        return password_bytes
