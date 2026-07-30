"""Integration tests for SQLAlchemyUserRepository."""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.identity.entities import (
    Permission,
    Role,
    User,
)
from app.domain.identity.enums import UserStatus
from app.domain.identity.protocols import UserRepository
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.infrastructure.persistence import (
    Base,
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.identity import (
    PermissionModel,
    RoleModel,
    SQLAlchemyUserRepository,
    UserModel,
)


USER_ID = UserId(
    UUID("00000000-0000-0000-0000-000000000001")
)


@pytest.fixture
def engine() -> Iterator[Engine]:
    database_engine = create_database_engine(
        "sqlite+pysqlite:///:memory:"
    )
    Base.metadata.create_all(database_engine)

    try:
        yield database_engine
    finally:
        Base.metadata.drop_all(database_engine)
        database_engine.dispose()


@pytest.fixture
def session_factory(
    engine: Engine,
) -> sessionmaker[Session]:
    return create_session_factory(engine)


@pytest.fixture
def repository(
    session_factory: sessionmaker[Session],
) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session_factory)


def make_permission(name: str) -> Permission:
    return Permission(PermissionName(name))


def make_role(
    name: str,
    *permission_names: str,
) -> Role:
    return Role(
        name=RoleName(name),
        permissions=frozenset(
            make_permission(permission_name)
            for permission_name in permission_names
        ),
    )


def make_user(
    *,
    username: str = "administrator",
    email: str = "administrator@example.com",
    status: UserStatus = UserStatus.ACTIVE,
    roles: frozenset[Role] | None = None,
) -> User:
    if roles is None:
        roles = frozenset(
            {
                make_role(
                    "administrator",
                    "dashboard.read",
                    "streams.manage",
                )
            }
        )

    return User(
        id=USER_ID,
        username=Username(username),
        email=Email(email),
        password_hash=PasswordHash(
            "$2b$12$abcdefghijklmnopqrstuu"
            "abcdefghijklmnopqrstuu1234567890"
        ),
        roles=roles,
        status=status,
    )


def test_implements_user_repository_protocol(
    repository: SQLAlchemyUserRepository,
) -> None:
    assert isinstance(repository, UserRepository)


def test_save_and_get_by_id(
    repository: SQLAlchemyUserRepository,
) -> None:
    user = make_user()

    repository.save(user)

    assert repository.get_by_id(user.id) == user


def test_save_and_get_by_username(
    repository: SQLAlchemyUserRepository,
) -> None:
    user = make_user()

    repository.save(user)

    assert repository.get_by_username(user.username) == user


def test_get_by_id_returns_none_for_unknown_user(
    repository: SQLAlchemyUserRepository,
) -> None:
    unknown_id = UserId(
        UUID("00000000-0000-0000-0000-000000000099")
    )

    assert repository.get_by_id(unknown_id) is None


def test_get_by_username_returns_none_for_unknown_user(
    repository: SQLAlchemyUserRepository,
) -> None:
    assert (
        repository.get_by_username(
            Username("unknown-user")
        )
        is None
    )


def test_save_persists_roles_and_permissions(
    repository: SQLAlchemyUserRepository,
) -> None:
    user = make_user(
        roles=frozenset(
            {
                make_role(
                    "administrator",
                    "dashboard.read",
                    "streams.manage",
                ),
                make_role(
                    "operator",
                    "dashboard.read",
                ),
            }
        )
    )

    repository.save(user)

    restored = repository.get_by_id(user.id)

    assert restored == user
    assert restored is not None
    assert len(restored.roles) == 2
    assert restored.has_permission_name(
        PermissionName("streams.manage")
    )


def test_save_updates_existing_user(
    repository: SQLAlchemyUserRepository,
) -> None:
    original = make_user()
    repository.save(original)

    updated = make_user(
        username="noc-administrator",
        email="noc-administrator@example.com",
        status=UserStatus.LOCKED,
        roles=frozenset(
            {
                make_role(
                    "operator",
                    "dashboard.read",
                )
            }
        ),
    )

    repository.save(updated)

    restored = repository.get_by_id(USER_ID)

    assert restored == updated
    assert restored is not None
    assert restored.status is UserStatus.LOCKED
    assert not restored.has_role_name(
        RoleName("administrator")
    )
    assert restored.has_role_name(RoleName("operator"))


def test_save_reuses_shared_role_and_permission_rows(
    repository: SQLAlchemyUserRepository,
    session_factory: sessionmaker[Session],
) -> None:
    shared_role = make_role(
        "operator",
        "dashboard.read",
    )

    first_user = make_user(
        roles=frozenset({shared_role})
    )

    second_user = User(
        id=UserId(
            UUID("00000000-0000-0000-0000-000000000002")
        ),
        username=Username("second-operator"),
        email=Email("second-operator@example.com"),
        password_hash=first_user.password_hash,
        roles=frozenset({shared_role}),
        status=UserStatus.ACTIVE,
    )

    repository.save(first_user)
    repository.save(second_user)

    with session_factory() as session:
        role_count = session.scalar(
            select(func.count()).select_from(RoleModel)
        )
        permission_count = session.scalar(
            select(func.count()).select_from(
                PermissionModel
            )
        )
        user_count = session.scalar(
            select(func.count()).select_from(UserModel)
        )

    assert role_count == 1
    assert permission_count == 1
    assert user_count == 2


def test_retrieved_user_is_detached_domain_entity(
    repository: SQLAlchemyUserRepository,
) -> None:
    user = make_user()
    repository.save(user)

    restored = repository.get_by_id(user.id)

    assert isinstance(restored, User)
    assert not isinstance(restored, UserModel)


@pytest.mark.parametrize(
    ("method_name", "invalid_value"),
    [
        ("get_by_id", "not-a-user-id"),
        ("get_by_username", "administrator"),
        ("save", object()),
    ],
)
def test_rejects_invalid_domain_arguments(
    repository: SQLAlchemyUserRepository,
    method_name: str,
    invalid_value: object,
) -> None:
    method = getattr(repository, method_name)

    with pytest.raises(TypeError):
        method(invalid_value)
