from dataclasses import dataclass
from unicodedata import category


@dataclass(frozen=True, slots=True)
class Username:
    """Immutable username used to identify a user within the IAM domain."""

    MIN_LENGTH = 3
    MAX_LENGTH = 64

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Username value must be a string")

        normalized_value = self.value.strip()

        if len(normalized_value) < self.MIN_LENGTH:
            raise ValueError(
                f"Username must contain at least {self.MIN_LENGTH} characters"
            )

        if len(normalized_value) > self.MAX_LENGTH:
            raise ValueError(
                f"Username must contain at most {self.MAX_LENGTH} characters"
            )

        if any(category(character).startswith("C") for character in normalized_value):
            raise ValueError("Username must not contain control characters")

        object.__setattr__(self, "value", normalized_value)

    def __str__(self) -> str:
        return self.value
