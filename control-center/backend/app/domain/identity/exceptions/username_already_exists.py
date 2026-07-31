from app.domain.identity.exceptions.identity_error import IdentityError


class UsernameAlreadyExists(IdentityError):
    """Raised when a username is already registered."""
