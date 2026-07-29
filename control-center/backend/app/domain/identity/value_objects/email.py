from dataclasses import dataclass
from unicodedata import category


@dataclass(frozen=True, slots=True)
class Email:
    """Immutable email address used within the IAM domain."""

    MAX_LENGTH = 254

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Email value must be a string")

        normalized_value = self.value.strip()

        if not normalized_value:
            raise ValueError("Email value must not be empty")

        if len(normalized_value) > self.MAX_LENGTH:
            raise ValueError(
                f"Email must contain at most {self.MAX_LENGTH} characters"
            )

        if any(character.isspace() for character in normalized_value):
            raise ValueError("Email must not contain whitespace")

        if any(category(character).startswith("C") for character in normalized_value):
            raise ValueError("Email must not contain control characters")

        if normalized_value.count("@") != 1:
            raise ValueError("Email must contain exactly one @ character")

        local_part, domain_part = normalized_value.split("@")

        if not local_part:
            raise ValueError("Email local part must not be empty")

        if not domain_part:
            raise ValueError("Email domain must not be empty")

        if "." not in domain_part:
            raise ValueError("Email domain must contain at least one dot")

        if domain_part.startswith(".") or domain_part.endswith("."):
            raise ValueError("Email domain dot placement is invalid")

        object.__setattr__(self, "value", normalized_value)

    def __str__(self) -> str:
        return self.value
