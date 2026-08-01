"""Tests for SQLAlchemyIdentityCatalogRepository."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.domain.identity.entities import Permission, Role
from app.domain.identity.value_objects import (
    PermissionName,
    RoleName,
)
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.identity.models import Base
from app.infrastructure.persistence.identity.sqlalchemy_identity_catalog_repository import (
    SQLAlchemyIdentityCatalogRepository,
)


@pytest.fixture
def session_factory(
    tmp_path: Path,
) -> sessionmaker[Session]:
    database_path = tmp_path / "identity-catalog.db"

    engine = create_database_engine(
        f"sqlite:///{database_path}",
        echo=False,
    )

    Base.metadata.create_all(bind=engine)

    return create_session_factory(engine)


@pytest.fixture
def repository(
    session_factory: sessionmaker[Session],
) -> SQLAlchemyIdentityCatalogRepository:
    return SQLAlchemyIdentityCatalogRepository(
        session_factory
    )


def make_role(
    *,
    name: str = "operator",
    permissions: tuple[str, ...] = (
        "system.read",
        "streaming.read",
    ),
) -> Role:
    return Role(
        name=RoleName(name),
        permissions=frozenset(
            Permission(
                name=PermissionName(permission)
            )
            for permission in permissions
        ),
    )


def test_save_and_get_role(
    repository: SQLAlchemyIdentityCatalogRepository,
) -> None:
    role = make_role()

    repository.save_role(role)

    assert repository.get_role(role.name) == role


def test_get_role_returns_none_when_unknown(
    repository: SQLAlchemyIdentityCatalogRepository,
) -> None:
    assert (
        repository.get_role(
            RoleName("unknown")
        )
        is None
    )


def test_list_roles_returns_deterministic_order(
    repository: SQLAlchemyIdentityCatalogRepository,
) -> None:
    repository.save_role(
        make_role(name="viewer")
    )
    repository.save_role(
        make_role(name="administrator")
    )
    repository.save_role(
        make_role(name="operator")
    )

    assert [
        role.name.value
        for role in repository.list_roles()
    ] == [
        "administrator",
        "operator",
        "viewer",
    ]


def test_save_role_is_idempotent(
    repository: SQLAlchemyIdentityCatalogRepository,
) -> None:
    role = make_role()

    repository.save_role(role)
    repository.save_role(role)

    assert repository.list_roles() == (role,)


def test_save_role_replaces_permission_assignments(
    repository: SQLAlchemyIdentityCatalogRepository,
) -> None:
    original = make_role(
        permissions=(
            "system.read",
            "streaming.read",
        )
    )

    updated = make_role(
        permissions=(
            "dashboard.read",
            "alarms.read",
        )
    )

    repository.save_role(original)
    repository.save_role(updated)

    restored = repository.get_role(
        RoleName("operator")
    )

    assert restored == updated

    assert {
        permission.name.value
        for permission in restored.permissions
    } == {
        "dashboard.read",
        "alarms.read",
    }


def test_save_role_reuses_existing_permissions(
    repository: SQLAlchemyIdentityCatalogRepository,
) -> None:
    operator = make_role(
        name="operator",
        permissions=(
            "system.read",
            "streaming.read",
        ),
    )

    viewer = make_role(
        name="viewer",
        permissions=(
            "system.read",
        ),
    )

    repository.save_role(operator)
    repository.save_role(viewer)

    roles = repository.list_roles()

    assert len(roles) == 2

    assert {
        role.name.value
        for role in roles
    } == {
        "operator",
        "viewer",
    }


@pytest.mark.parametrize(
    (
        "method_name",
        "argument",
    ),
    [
        (
            "get_role",
            "operator",
        ),
        (
            "save_role",
            "operator",
        ),
    ],
)
def test_repository_rejects_invalid_arguments(
    repository: SQLAlchemyIdentityCatalogRepository,
    method_name: str,
    argument: object,
) -> None:
    with pytest.raises(TypeError):
        getattr(repository, method_name)(
            argument
        )
