from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class UserId:
    """Immutable identifier for a user in the IAM domain."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise TypeError("UserId value must be a UUID")

    @classmethod
    def generate(cls) -> "UserId":
        """Create a new UserId."""

        return cls(uuid4())

    @classmethod
    def from_string(cls, value: str) -> "UserId":
        """Reconstruct a UserId from its string representation."""

        if not isinstance(value, str):
            raise TypeError("UserId string value must be a string")

        try:
            parsed_value = UUID(value)
        except ValueError as error:
            raise ValueError("Invalid UserId value") from error

        return cls(parsed_value)

    def __str__(self) -> str:
        return str(self.value)
