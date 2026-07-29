from app.domain.identity.exceptions.identity_error import IdentityError


class UserNotFound(IdentityError):
    """Raised when a requested user does not exist."""
