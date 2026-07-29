from app.domain.identity.exceptions.identity_error import IdentityError


class UserLocked(IdentityError):
    """Raised when an operation is attempted by a locked user."""
