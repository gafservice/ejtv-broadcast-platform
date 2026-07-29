from dataclasses import dataclass
from re import fullmatch


@dataclass(frozen=True, slots=True)
class PermissionName:
    """Immutable hierarchical permission name used by the IAM domain."""

    MIN_LENGTH = 3
    MAX_LENGTH = 128
    PATTERN = r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+"

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("PermissionName value must be a string")

        normalized_value = self.value.strip()

        if len(normalized_value) < self.MIN_LENGTH:
            raise ValueError(
                f"PermissionName must contain at least "
                f"{self.MIN_LENGTH} characters"
            )

        if len(normalized_value) > self.MAX_LENGTH:
            raise ValueError(
                f"PermissionName must contain at most "
                f"{self.MAX_LENGTH} characters"
            )

        if fullmatch(self.PATTERN, normalized_value) is None:
            raise ValueError(
                "PermissionName must contain at least two lowercase "
                "segments separated by dots; each segment must start "
                "with a lowercase letter and contain only lowercase "
                "letters, numbers, and underscores"
            )

        object.__setattr__(self, "value", normalized_value)

    def __str__(self) -> str:
        return self.value
