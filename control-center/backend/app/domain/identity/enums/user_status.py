from enum import StrEnum


class UserStatus(StrEnum):
    """Operational status of a user within the IAM domain."""

    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"
