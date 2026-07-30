"""JWT implementation of the authentication-token domain contract."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.domain.identity.entities import AuthenticatedIdentity
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
    UserId,
    Username,
)


class JWTTokenProvider:
    """Issue and verify signed JSON Web Tokens.

    Configuration is injected through the constructor so this adapter
    remains independent from application settings and environment variables.
    """

    ALGORITHM = "HS256"
    MIN_SECRET_BYTES = 32

    REQUIRED_CLAIMS = [
        "sub",
        "username",
        "roles",
        "permissions",
        "iat",
        "nbf",
        "exp",
        "iss",
        "aud",
        "jti",
    ]

    def __init__(
        self,
        *,
        secret_key: str,
        issuer: str,
        audience: str,
        expiration_seconds: int = 900,
        leeway_seconds: int = 0,
    ) -> None:
        self._secret_key = self._validate_secret_key(secret_key)
        self._issuer = self._validate_text(issuer, "issuer")
        self._audience = self._validate_text(audience, "audience")
        self._expiration_seconds = self._validate_non_negative_integer(
            expiration_seconds,
            "expiration_seconds",
            allow_zero=False,
        )
        self._leeway_seconds = self._validate_non_negative_integer(
            leeway_seconds,
            "leeway_seconds",
            allow_zero=True,
        )

    @property
    def issuer(self) -> str:
        """Return the configured token issuer."""
        return self._issuer

    @property
    def audience(self) -> str:
        """Return the configured token audience."""
        return self._audience

    @property
    def expiration_seconds(self) -> int:
        """Return token lifetime in seconds."""
        return self._expiration_seconds

    @property
    def leeway_seconds(self) -> int:
        """Return the accepted clock-skew margin in seconds."""
        return self._leeway_seconds

    def issue(self, identity: AuthenticatedIdentity) -> str:
        """Issue a signed JWT representing an authenticated identity."""
        if not isinstance(identity, AuthenticatedIdentity):
            raise TypeError(
                "identity must be an AuthenticatedIdentity"
            )

        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + timedelta(
            seconds=self._expiration_seconds
        )

        claims = {
            "sub": str(identity.user_id),
            "username": identity.username.value,
            "roles": sorted(role.value for role in identity.roles),
            "permissions": sorted(
                permission.value
                for permission in identity.permissions
            ),
            "iat": issued_at,
            "nbf": issued_at,
            "exp": expires_at,
            "iss": self._issuer,
            "aud": self._audience,
            "jti": str(uuid4()),
        }

        return jwt.encode(
            claims,
            self._secret_key,
            algorithm=self.ALGORITHM,
        )

    def verify(
        self,
        token: str,
    ) -> AuthenticatedIdentity | None:
        """Return the identity represented by a valid JWT."""
        if not isinstance(token, str) or not token.strip():
            return None

        try:
            claims = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self.ALGORITHM],
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway_seconds,
                options={
                    "require": self.REQUIRED_CLAIMS,
                    "strict_aud": True,
                },
            )

            return self._identity_from_claims(claims)
        except (
            jwt.InvalidTokenError,
            KeyError,
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _identity_from_claims(
        claims: dict[str, object],
    ) -> AuthenticatedIdentity:
        roles_claim = claims["roles"]
        permissions_claim = claims["permissions"]

        if not isinstance(roles_claim, list):
            raise TypeError("roles claim must be a list")

        if not isinstance(permissions_claim, list):
            raise TypeError("permissions claim must be a list")

        if not all(isinstance(role, str) for role in roles_claim):
            raise TypeError("every role claim must be a string")

        if not all(
            isinstance(permission, str)
            for permission in permissions_claim
        ):
            raise TypeError(
                "every permission claim must be a string"
            )

        subject = claims["sub"]
        username = claims["username"]

        if not isinstance(subject, str):
            raise TypeError("sub claim must be a string")

        if not isinstance(username, str):
            raise TypeError("username claim must be a string")

        return AuthenticatedIdentity(
            user_id=UserId.from_string(subject),
            username=Username(username),
            roles=frozenset(
                RoleName(role)
                for role in roles_claim
            ),
            permissions=frozenset(
                PermissionName(permission)
                for permission in permissions_claim
            ),
        )

    @classmethod
    def _validate_secret_key(cls, secret_key: str) -> str:
        if not isinstance(secret_key, str):
            raise TypeError("secret_key must be a string")

        if len(secret_key.encode("utf-8")) < cls.MIN_SECRET_BYTES:
            raise ValueError(
                "secret_key must contain at least "
                f"{cls.MIN_SECRET_BYTES} UTF-8 bytes"
            )

        return secret_key

    @staticmethod
    def _validate_text(value: str, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")

        normalized = value.strip()

        if not normalized:
            raise ValueError(f"{field_name} must not be empty")

        return normalized

    @staticmethod
    def _validate_non_negative_integer(
        value: int,
        field_name: str,
        *,
        allow_zero: bool,
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{field_name} must be an integer")

        minimum = 0 if allow_zero else 1

        if value < minimum:
            comparator = "non-negative" if allow_zero else "positive"
            raise ValueError(
                f"{field_name} must be a {comparator} integer"
            )

        return value
