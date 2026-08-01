from app.domain.identity.exceptions.identity_error import (
    IdentityError,
)


class CannotDisableLastAdministrator(IdentityError):
    """Raised when disabling or locking the last active administrator."""
