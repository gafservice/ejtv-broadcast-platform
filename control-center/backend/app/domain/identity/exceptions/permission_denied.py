from app.domain.identity.exceptions.identity_error import IdentityError


class PermissionDenied(IdentityError):
    """Raised when an identity lacks a required permission."""
