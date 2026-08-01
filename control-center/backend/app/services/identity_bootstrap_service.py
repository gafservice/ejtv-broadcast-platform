"""Application service for bootstrapping the Identity subsystem."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.identity.catalog import (
    ADMINISTRATOR_ROLE,
    DEFAULT_ROLES,
    RoleDefinition,
)
from app.domain.identity.entities import (
    AuthenticatedIdentity,
    Permission,
    Role,
    User,
)
from app.domain.identity.protocols import (
    AuditRepository,
    IdentityCatalogRepository,
    PasswordHasher,
    UserRepository,
)
from app.domain.identity.value_objects import (
    Email,
    UserId,
    Username,
)


class BootstrapStatus(StrEnum):
    """Possible outcomes of an Identity bootstrap execution."""

    CREATED = "created"
    ALREADY_EXISTS = "already_exists"


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Result returned by the Identity bootstrap process."""

    status: BootstrapStatus
    user: User

    @property
    def created(self) -> bool:
        """Return whether the administrator was created."""

        return self.status is BootstrapStatus.CREATED


class CatalogRoleStatus(StrEnum):
    """Possible outcomes when synchronizing a canonical role."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class CatalogSynchronizationResult:
    """Summary of canonical Identity catalog synchronization."""

    created: tuple[str, ...]
    updated: tuple[str, ...]
    unchanged: tuple[str, ...]

    @property
    def changed(self) -> bool:
        """Return whether persistence was modified."""

        return bool(self.created or self.updated)

    @property
    def total(self) -> int:
        """Return the total number of canonical roles."""

        return (
            len(self.created)
            + len(self.updated)
            + len(self.unchanged)
        )


@dataclass(frozen=True, slots=True)
class CatalogIntegrityResult:
    """Result of validating the persisted Identity catalog."""

    missing_roles: tuple[str, ...]
    unexpected_roles: tuple[str, ...]
    mismatched_roles: tuple[str, ...]

    @property
    def valid(self) -> bool:
        """Return whether the persisted catalog is canonical."""

        return not (
            self.missing_roles
            or self.unexpected_roles
            or self.mismatched_roles
        )


class IdentityBootstrapService:
    """Create the initial administrator account when it does not exist."""

    def __init__(
        self,
        *,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        audit_repository: AuditRepository,
        catalog_repository: (
            IdentityCatalogRepository | None
        ) = None,
    ) -> None:
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._audit_repository = audit_repository
        self._catalog_repository = catalog_repository

    def verify_integrity(
        self,
    ) -> CatalogIntegrityResult:
        """Validate the persisted catalog without modifying it."""

        repository = self._require_catalog_repository()

        canonical_roles = {
            definition.name: self._build_role(definition)
            for definition in DEFAULT_ROLES
        }

        persisted_roles = {
            role.name: role
            for role in repository.list_roles()
        }

        missing_roles = tuple(
            sorted(
                role_name.value
                for role_name in (
                    canonical_roles.keys()
                    - persisted_roles.keys()
                )
            )
        )

        unexpected_roles = tuple(
            sorted(
                role_name.value
                for role_name in (
                    persisted_roles.keys()
                    - canonical_roles.keys()
                )
            )
        )

        mismatched_roles = tuple(
            sorted(
                role_name.value
                for role_name in (
                    canonical_roles.keys()
                    & persisted_roles.keys()
                )
                if canonical_roles[role_name]
                != persisted_roles[role_name]
            )
        )

        result = CatalogIntegrityResult(
            missing_roles=missing_roles,
            unexpected_roles=unexpected_roles,
            mismatched_roles=mismatched_roles,
        )

        self._audit_repository.record(
            "identity.bootstrap.integrity_verified",
            None,
            {
                "valid": str(result.valid).lower(),
                "missing_roles": ",".join(
                    result.missing_roles
                ),
                "unexpected_roles": ",".join(
                    result.unexpected_roles
                ),
                "mismatched_roles": ",".join(
                    result.mismatched_roles
                ),
            },
        )

        return result

    def synchronize_catalog(
        self,
    ) -> CatalogSynchronizationResult:
        """Create or repair all canonical roles and permissions."""

        repository = self._require_catalog_repository()

        created: list[str] = []
        updated: list[str] = []
        unchanged: list[str] = []

        for definition in sorted(
            DEFAULT_ROLES,
            key=lambda item: item.name.value,
        ):
            canonical_role = self._build_role(definition)

            persisted_role = repository.get_role(
                canonical_role.name
            )

            if persisted_role is None:
                repository.save_role(canonical_role)
                created.append(canonical_role.name.value)

                self._audit_repository.record(
                    "identity.bootstrap.role_created",
                    None,
                    {
                        "role": canonical_role.name.value,
                    },
                )

                continue

            if persisted_role != canonical_role:
                repository.save_role(canonical_role)
                updated.append(canonical_role.name.value)

                self._audit_repository.record(
                    "identity.bootstrap.role_updated",
                    None,
                    {
                        "role": canonical_role.name.value,
                    },
                )

                continue

            unchanged.append(canonical_role.name.value)

        result = CatalogSynchronizationResult(
            created=tuple(created),
            updated=tuple(updated),
            unchanged=tuple(unchanged),
        )

        self._audit_repository.record(
            "identity.bootstrap.catalog_synchronized",
            None,
            {
                "created": ",".join(result.created),
                "updated": ",".join(result.updated),
                "unchanged": ",".join(result.unchanged),
                "total": str(result.total),
            },
        )

        return result

    def bootstrap_administrator(
        self,
        *,
        username: str,
        email: str,
        password: str,
    ) -> BootstrapResult:
        """
        Create the initial administrator account.

        Repeated executions are idempotent: an existing username is returned
        without changing its password, email, roles or status.
        """

        username_value = Username(username)

        existing_user = self._user_repository.get_by_username(
            username_value
        )

        if existing_user is not None:
            self._audit_repository.record(
                "identity.bootstrap.skipped",
                AuthenticatedIdentity.from_user(existing_user),
                {
                    "username": existing_user.username.value,
                    "reason": "administrator_already_exists",
                },
            )

            return BootstrapResult(
                status=BootstrapStatus.ALREADY_EXISTS,
                user=existing_user,
            )

        administrator_role = self._build_administrator_role()

        user = User(
            id=UserId.generate(),
            username=username_value,
            email=Email(email),
            password_hash=self._password_hasher.hash(password),
            roles=frozenset({administrator_role}),
        )

        self._user_repository.save(user)

        self._audit_repository.record(
            "identity.bootstrap.administrator_created",
            AuthenticatedIdentity.from_user(user),
            {
                "username": user.username.value,
                "role": administrator_role.name.value,
            },
        )

        return BootstrapResult(
            status=BootstrapStatus.CREATED,
            user=user,
        )

    def _require_catalog_repository(
        self,
    ) -> IdentityCatalogRepository:
        """Return the configured catalog repository."""

        if self._catalog_repository is None:
            raise RuntimeError(
                "catalog_repository is required "
                "to synchronize the Identity catalog"
            )

        return self._catalog_repository

    @staticmethod
    def _build_role(
        definition: RoleDefinition,
    ) -> Role:
        """Build a domain role from a canonical definition."""

        if not isinstance(definition, RoleDefinition):
            raise TypeError(
                "definition must be a RoleDefinition"
            )

        return Role(
            name=definition.name,
            permissions=frozenset(
                Permission(name=permission_name)
                for permission_name in definition.permissions
            ),
        )

    @staticmethod
    def _build_administrator_role() -> Role:
        """Build the administrator role from the canonical catalog."""

        return IdentityBootstrapService._build_role(
            ADMINISTRATOR_ROLE
        )
