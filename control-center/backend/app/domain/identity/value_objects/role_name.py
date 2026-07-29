from dataclasses import dataclass
from re import fullmatch


@dataclass(frozen=True, slots=True)
class RoleName:
    """Immutable role name used within the IAM domain."""

    MIN_LENGTH = 3
    MAX_LENGTH = 64
    PATTERN = r"[a-z][a-z0-9_]{2,63}"

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("RoleName value must be a string")

        normalized_value = self.value.strip()

        if len(normalized_value) < self.MIN_LENGTH:
            raise ValueError(
                f"RoleName must contain at least {self.MIN_LENGTH} characters"
            )

        if len(normalized_value) > self.MAX_LENGTH:
            raise ValueError(
                f"RoleName must contain at most {self.MAX_LENGTH} characters"
            )

        if fullmatch(self.PATTERN, normalized_value) is None:
            raise ValueError(
                "RoleName must start with a lowercase letter and contain only "
                "lowercase letters, numbers, and underscores"
            )

        object.__setattr__(self, "value", normalized_value)

    def __str__(self) -> str:
        return self.value
