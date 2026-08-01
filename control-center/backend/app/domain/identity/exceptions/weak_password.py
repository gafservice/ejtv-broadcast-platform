from app.domain.identity.exceptions.identity_error import (
    IdentityError,
)


class WeakPassword(IdentityError):
    """Raised when a password violates the security policy."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
