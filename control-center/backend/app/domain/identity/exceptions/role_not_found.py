from app.domain.identity.exceptions.identity_error import (
    IdentityError,
)


class RoleNotFound(IdentityError):
    """Raised when a requested role does not exist."""
