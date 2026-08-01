"""Tests for the Identity bootstrap application service."""

import pytest

from app.domain.identity.catalog import DEFAULT_ROLES
from app.domain.identity.entities import (
    Permission,
    Role,
    User,
)
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from collections.abc import Mapping

from app.domain.identity.entities import AuthenticatedIdentity
from app.services.identity_bootstrap_service import (
    BootstrapStatus,
    CatalogIntegrityResult,
    CatalogSynchronizationResult,
    IdentityBootstrapService,
)


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.saved_users: list[User] = []

    def get_by_id(self, user_id):
        return next(
            (
                user
                for user in self.users.values()
                if user.id == user_id
            ),
            None,
        )

    def get_by_username(
        self,
        username: Username,
    ) -> User | None:
        return self.users.get(username.value)

    def save(self, user: User) -> None:
        self.users[user.username.value] = user
        self.saved_users.append(user)


class FakePasswordHasher:
    def __init__(self) -> None:
        self.hashed_passwords: list[str] = []

    def hash(self, plain_password: str) -> PasswordHash:
        self.hashed_passwords.append(plain_password)
        return PasswordHash("$2b$12$bootstrap_test_hash_value")

    def verify(
        self,
        plain_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        return False


class FakeAuditRepository:
    def __init__(self) -> None:
        self.records: list[
            tuple[
                str,
                AuthenticatedIdentity | None,
                Mapping[str, str] | None,
            ]
        ] = []

    def record(
        self,
        event_type: str,
        identity: AuthenticatedIdentity | None,
        details: Mapping[str, str] | None = None,
    ) -> None:
        self.records.append(
            (event_type, identity, details)
        )


def build_service():
    user_repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    audit_repository = FakeAuditRepository()

    service = IdentityBootstrapService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        audit_repository=audit_repository,
    )

    return (
        service,
        user_repository,
        password_hasher,
        audit_repository,
    )


def test_bootstrap_creates_administrator() -> None:
    (
        service,
        user_repository,
        password_hasher,
        audit_repository,
    ) = build_service()

    result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    assert result.status is BootstrapStatus.CREATED
    assert result.created is True
    assert result.user.username.value == "administrator"
    assert result.user.email.value == "admin@example.com"
    assert result.user.is_active()
    assert len(user_repository.saved_users) == 1
    assert password_hasher.hashed_passwords == [
        "ChangeMeNow123!"
    ]
    assert audit_repository.records[0][0] == (
        "identity.bootstrap.administrator_created"
    )


def test_bootstrap_assigns_administrator_role() -> None:
    service, _, _, _ = build_service()

    result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    role_names = {
        role.name.value
        for role in result.user.roles
    }

    assert role_names == {"administrator"}


def test_bootstrap_assigns_all_catalog_permissions() -> None:
    service, _, _, _ = build_service()

    result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    permissions = {
        permission.name.value
        for role in result.user.roles
        for permission in role.permissions
    }

    assert permissions == {
        "system.read",
        "system.write",
        "dashboard.read",
        "dashboard.write",
        "streaming.read",
        "streaming.write",
        "identity.read",
        "identity.write",
        "users.read",
        "users.write",
        "users.manage",
        "roles.read",
        "roles.write",
        "alarms.read",
        "alarms.write",
    }


def test_bootstrap_is_idempotent() -> None:
    (
        service,
        user_repository,
        password_hasher,
        audit_repository,
    ) = build_service()

    first_result = service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="InitialPassword123!",
    )

    second_result = service.bootstrap_administrator(
        username="administrator",
        email="different@example.com",
        password="DifferentPassword123!",
    )

    assert first_result.status is BootstrapStatus.CREATED
    assert second_result.status is BootstrapStatus.ALREADY_EXISTS
    assert second_result.created is False
    assert second_result.user == first_result.user
    assert len(user_repository.saved_users) == 1
    assert password_hasher.hashed_passwords == [
        "InitialPassword123!"
    ]
    assert audit_repository.records[-1][0] == (
        "identity.bootstrap.skipped"
    )


def test_existing_user_is_not_modified() -> None:
    service, user_repository, _, _ = build_service()

    original_result = service.bootstrap_administrator(
        username="administrator",
        email="original@example.com",
        password="InitialPassword123!",
    )

    repeated_result = service.bootstrap_administrator(
        username="administrator",
        email="changed@example.com",
        password="ChangedPassword123!",
    )

    assert repeated_result.user.email.value == (
        "original@example.com"
    )
    assert (
        repeated_result.user.password_hash
        == original_result.user.password_hash
    )
    assert len(user_repository.saved_users) == 1


def test_created_audit_contains_identity_and_role() -> None:
    service, _, _, audit_repository = build_service()

    service.bootstrap_administrator(
        username="administrator",
        email="admin@example.com",
        password="ChangeMeNow123!",
    )

    event_type, identity, details = audit_repository.records[0]

    assert event_type == (
        "identity.bootstrap.administrator_created"
    )
    assert identity is not None
    assert identity.username.value == "administrator"
    assert details == {
        "username": "administrator",
        "role": "administrator",
    }


class FakeIdentityCatalogRepository:
    """Repositorio en memoria para probar el catálogo canónico."""

    def __init__(
        self,
        roles: tuple[Role, ...] = (),
    ) -> None:
        self.roles = {
            role.name: role
            for role in roles
        }
        self.saved_roles: list[Role] = []

    def get_role(
        self,
        role_name: RoleName,
    ) -> Role | None:
        return self.roles.get(role_name)

    def list_roles(self) -> tuple[Role, ...]:
        return tuple(
            sorted(
                self.roles.values(),
                key=lambda role: role.name.value,
            )
        )

    def save_role(
        self,
        role: Role,
    ) -> None:
        self.roles[role.name] = role
        self.saved_roles.append(role)


def make_catalog_role(
    role_name: str,
    *permission_names: str,
) -> Role:
    return Role(
        name=RoleName(role_name),
        permissions=frozenset(
            Permission(
                name=PermissionName(permission_name)
            )
            for permission_name in permission_names
        ),
    )


def build_bootstrap_service_with_catalog(
    *,
    roles: tuple[Role, ...] = (),
) -> tuple[
    IdentityBootstrapService,
    FakeIdentityCatalogRepository,
    FakeAuditRepository,
]:
    user_repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    audit_repository = FakeAuditRepository()
    catalog_repository = FakeIdentityCatalogRepository(
        roles
    )

    service = IdentityBootstrapService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        audit_repository=audit_repository,
        catalog_repository=catalog_repository,
    )

    return (
        service,
        catalog_repository,
        audit_repository,
    )


def test_synchronize_catalog_creates_missing_roles() -> None:
    (
        service,
        catalog_repository,
        audit_repository,
    ) = build_bootstrap_service_with_catalog()

    result = service.synchronize_catalog()

    assert result.created == (
        "administrator",
        "operator",
        "viewer",
    )
    assert result.updated == ()
    assert result.unchanged == ()
    assert result.changed is True
    assert result.total == 3

    assert [
        role.name.value
        for role in catalog_repository.saved_roles
    ] == [
        "administrator",
        "operator",
        "viewer",
    ]

    assert [
        event[0]
        for event in audit_repository.records
    ] == [
        "identity.bootstrap.role_created",
        "identity.bootstrap.role_created",
        "identity.bootstrap.role_created",
        "identity.bootstrap.catalog_synchronized",
    ]


def test_synchronize_catalog_updates_modified_role() -> None:
    modified_operator = make_catalog_role(
        "operator",
        "system.read",
    )

    (
        service,
        catalog_repository,
        audit_repository,
    ) = build_bootstrap_service_with_catalog(
        roles=(
            modified_operator,
        )
    )

    result = service.synchronize_catalog()

    assert result.created == (
        "administrator",
        "viewer",
    )
    assert result.updated == (
        "operator",
    )
    assert result.unchanged == ()

    restored_operator = catalog_repository.get_role(
        RoleName("operator")
    )

    assert {
        permission.name.value
        for permission in restored_operator.permissions
    } == {
        "system.read",
        "dashboard.read",
        "streaming.read",
        "streaming.write",
        "alarms.read",
        "alarms.write",
    }

    assert any(
        event_type == "identity.bootstrap.role_updated"
        and details == {"role": "operator"}
        for event_type, _, details
        in audit_repository.records
    )


def test_synchronize_catalog_leaves_valid_roles_unchanged() -> None:
    canonical_roles = tuple(
        IdentityBootstrapService._build_role(
            definition
        )
        for definition in DEFAULT_ROLES
    )

    (
        service,
        catalog_repository,
        audit_repository,
    ) = build_bootstrap_service_with_catalog(
        roles=canonical_roles
    )

    result = service.synchronize_catalog()

    assert result.created == ()
    assert result.updated == ()
    assert result.unchanged == (
        "administrator",
        "operator",
        "viewer",
    )
    assert result.changed is False
    assert result.total == 3

    assert catalog_repository.saved_roles == []

    assert audit_repository.records == [
        (
            "identity.bootstrap.catalog_synchronized",
            None,
            {
                "created": "",
                "updated": "",
                "unchanged": (
                    "administrator,operator,viewer"
                ),
                "total": "3",
            },
        )
    ]


def test_synchronize_catalog_is_idempotent() -> None:
    (
        service,
        catalog_repository,
        audit_repository,
    ) = build_bootstrap_service_with_catalog()

    first = service.synchronize_catalog()
    saved_after_first = len(
        catalog_repository.saved_roles
    )

    second = service.synchronize_catalog()
    saved_after_second = len(
        catalog_repository.saved_roles
    )

    assert first.created == (
        "administrator",
        "operator",
        "viewer",
    )

    assert second.created == ()
    assert second.updated == ()
    assert second.unchanged == (
        "administrator",
        "operator",
        "viewer",
    )
    assert second.changed is False

    assert saved_after_first == 3
    assert saved_after_second == 3

    assert [
        event_type
        for event_type, _, _
        in audit_repository.records
    ].count(
        "identity.bootstrap.catalog_synchronized"
    ) == 2


def test_synchronize_catalog_requires_repository() -> None:
    service = IdentityBootstrapService(
        user_repository=FakeUserRepository(),
        password_hasher=FakePasswordHasher(),
        audit_repository=FakeAuditRepository(),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "catalog_repository is required "
            "to synchronize the Identity catalog"
        ),
    ):
        service.synchronize_catalog()


def test_catalog_synchronization_result_properties() -> None:
    result = CatalogSynchronizationResult(
        created=("operator",),
        updated=("viewer",),
        unchanged=("administrator",),
    )

    assert result.changed is True
    assert result.total == 3


def test_build_role_rejects_invalid_definition() -> None:
    with pytest.raises(
        TypeError,
        match="definition must be a RoleDefinition",
    ):
        IdentityBootstrapService._build_role(
            object()  # type: ignore[arg-type]
        )


def test_verify_integrity_accepts_canonical_catalog() -> None:
    canonical_roles = tuple(
        IdentityBootstrapService._build_role(
            definition
        )
        for definition in DEFAULT_ROLES
    )

    (
        service,
        _,
        audit_repository,
    ) = build_bootstrap_service_with_catalog(
        roles=canonical_roles
    )

    result = service.verify_integrity()

    assert result.valid is True
    assert result.missing_roles == ()
    assert result.unexpected_roles == ()
    assert result.mismatched_roles == ()

    assert audit_repository.records[-1] == (
        "identity.bootstrap.integrity_verified",
        None,
        {
            "valid": "true",
            "missing_roles": "",
            "unexpected_roles": "",
            "mismatched_roles": "",
        },
    )


def test_verify_integrity_detects_missing_roles() -> None:
    administrator = IdentityBootstrapService._build_role(
        next(
            definition
            for definition in DEFAULT_ROLES
            if definition.name.value == "administrator"
        )
    )

    (
        service,
        _,
        _,
    ) = build_bootstrap_service_with_catalog(
        roles=(administrator,)
    )

    result = service.verify_integrity()

    assert result.valid is False
    assert result.missing_roles == (
        "operator",
        "viewer",
    )
    assert result.unexpected_roles == ()
    assert result.mismatched_roles == ()


def test_verify_integrity_detects_unexpected_roles() -> None:
    canonical_roles = tuple(
        IdentityBootstrapService._build_role(
            definition
        )
        for definition in DEFAULT_ROLES
    )

    support_role = make_catalog_role(
        "support",
        "system.read",
    )

    (
        service,
        _,
        _,
    ) = build_bootstrap_service_with_catalog(
        roles=canonical_roles + (support_role,)
    )

    result = service.verify_integrity()

    assert result.valid is False
    assert result.missing_roles == ()
    assert result.unexpected_roles == (
        "support",
    )
    assert result.mismatched_roles == ()


def test_verify_integrity_detects_mismatched_roles() -> None:
    canonical_roles = tuple(
        IdentityBootstrapService._build_role(
            definition
        )
        for definition in DEFAULT_ROLES
        if definition.name.value != "operator"
    )

    modified_operator = make_catalog_role(
        "operator",
        "system.read",
    )

    (
        service,
        _,
        _,
    ) = build_bootstrap_service_with_catalog(
        roles=canonical_roles + (
            modified_operator,
        )
    )

    result = service.verify_integrity()

    assert result.valid is False
    assert result.missing_roles == ()
    assert result.unexpected_roles == ()
    assert result.mismatched_roles == (
        "operator",
    )


def test_verify_integrity_detects_multiple_problems() -> None:
    modified_administrator = make_catalog_role(
        "administrator",
        "system.read",
    )
    unexpected_role = make_catalog_role(
        "support",
        "system.read",
    )

    (
        service,
        _,
        _,
    ) = build_bootstrap_service_with_catalog(
        roles=(
            modified_administrator,
            unexpected_role,
        )
    )

    result = service.verify_integrity()

    assert result.valid is False
    assert result.missing_roles == (
        "operator",
        "viewer",
    )
    assert result.unexpected_roles == (
        "support",
    )
    assert result.mismatched_roles == (
        "administrator",
    )


def test_verify_integrity_requires_repository() -> None:
    service = IdentityBootstrapService(
        user_repository=FakeUserRepository(),
        password_hasher=FakePasswordHasher(),
        audit_repository=FakeAuditRepository(),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "catalog_repository is required "
            "to synchronize the Identity catalog"
        ),
    ):
        service.verify_integrity()
