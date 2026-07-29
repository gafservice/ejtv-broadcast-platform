from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """
    Represents an encoded password hash.

    Hash generation and password verification belong to a password
    hashing service, not to this value object.
    """

    MAX_LENGTH = 1024

    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("password hash must be a string")

        normalized = self.value.strip()

        if not normalized:
            raise ValueError("password hash must not be empty")

        if len(normalized) > self.MAX_LENGTH:
            raise ValueError(
                f"password hash must not exceed {self.MAX_LENGTH} characters"
            )

        if any(character.isspace() for character in normalized):
            raise ValueError(
                "password hash must not contain whitespace"
            )

        object.__setattr__(self, "value", normalized)
