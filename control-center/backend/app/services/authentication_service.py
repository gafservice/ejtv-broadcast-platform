from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.exceptions import (
    InvalidCredentials,
    UserDisabled,
    UserLocked,
)
from app.domain.identity.protocols import (
    AuditRepository,
    PasswordHasher,
    TokenProvider,
    UserRepository,
)
from app.domain.identity.value_objects import Username


class AuthenticationService:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_provider: TokenProvider,
        audit_repository: AuditRepository,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_provider = token_provider
        self._audit_repository = audit_repository

    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> str:
        username_value = Username(username)

        user = self._user_repository.get_by_username(
            username_value
        )

        if user is None:
            raise InvalidCredentials

        if user.is_locked():
            raise UserLocked

        if not user.is_active():
            raise UserDisabled

        if not self._password_hasher.verify(
            password,
            user.password_hash,
        ):
            raise InvalidCredentials

        identity = AuthenticatedIdentity.from_user(user)

        token = self._token_provider.issue(identity)

        self._audit_repository.record(
            "identity.login.succeeded",
            identity,
            {"username": user.username.value},
        )

        return token
