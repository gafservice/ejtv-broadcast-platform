"""Tests for the IdentityCatalogRepository protocol."""

from app.domain.identity.entities import Role
from app.domain.identity.protocols import (
    IdentityCatalogRepository,
)
from app.domain.identity.value_objects import RoleName


class FakeIdentityCatalogRepository:
    def __init__(self) -> None:
        self.roles: dict[RoleName, Role] = {}

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

    def save_role(self, role: Role) -> None:
        self.roles[role.name] = role


class IncompleteIdentityCatalogRepository:
    def get_role(
        self,
        role_name: RoleName,
    ) -> Role | None:
        return None


def test_fake_repository_implements_protocol() -> None:
    repository = FakeIdentityCatalogRepository()

    assert isinstance(
        repository,
        IdentityCatalogRepository,
    )


def test_incomplete_repository_does_not_implement_protocol() -> None:
    repository = IncompleteIdentityCatalogRepository()

    assert not isinstance(
        repository,
        IdentityCatalogRepository,
    )


def test_protocol_exposes_expected_operations() -> None:
    assert callable(
        getattr(IdentityCatalogRepository, "get_role")
    )
    assert callable(
        getattr(IdentityCatalogRepository, "list_roles")
    )
    assert callable(
        getattr(IdentityCatalogRepository, "save_role")
    )


def test_fake_repository_saves_and_returns_role() -> None:
    repository = FakeIdentityCatalogRepository()

    role = Role(
        name=RoleName("operator"),
    )

    repository.save_role(role)

    assert repository.get_role(role.name) == role
    assert repository.list_roles() == (role,)
