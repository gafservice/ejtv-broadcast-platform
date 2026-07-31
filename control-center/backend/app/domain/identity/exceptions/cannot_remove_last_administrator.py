from app.domain.identity.exceptions.identity_error import (
    IdentityError,
)


class CannotRemoveLastAdministrator(IdentityError):
    """Raised when removing the last administrator role."""
