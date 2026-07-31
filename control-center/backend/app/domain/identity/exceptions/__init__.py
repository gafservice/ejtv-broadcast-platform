from app.domain.identity.exceptions.email_already_exists import (
    EmailAlreadyExists,
)
from app.domain.identity.exceptions.identity_error import IdentityError
from app.domain.identity.exceptions.invalid_credentials import InvalidCredentials
from app.domain.identity.exceptions.permission_denied import PermissionDenied
from app.domain.identity.exceptions.user_disabled import UserDisabled
from app.domain.identity.exceptions.user_locked import UserLocked
from app.domain.identity.exceptions.user_not_found import UserNotFound
from app.domain.identity.exceptions.username_already_exists import (
    UsernameAlreadyExists,
)

__all__ = [
    "EmailAlreadyExists",
    "IdentityError",
    "InvalidCredentials",
    "PermissionDenied",
    "UserDisabled",
    "UserLocked",
    "UserNotFound",
    "UsernameAlreadyExists",
]
