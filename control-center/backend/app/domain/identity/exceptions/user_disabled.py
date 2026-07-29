from app.domain.identity.exceptions.identity_error import IdentityError


class UserDisabled(IdentityError):
    """Raised when an operation requires an enabled user."""
