from app.domain.identity.exceptions.identity_error import IdentityError


class EmailAlreadyExists(IdentityError):
    """Raised when an email address is already registered."""
