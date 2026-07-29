from app.domain.identity.exceptions.identity_error import IdentityError


class InvalidCredentials(IdentityError):
    """Raised when supplied authentication credentials are invalid."""
