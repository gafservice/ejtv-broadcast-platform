"""Tests for the UserRepository domain protocol."""

from __future__ import annotations

from app.domain.identity.entities import User
from app.domain.identity.protocols import UserRepository
from app.domain.identity.value_objects import UserId, Username


class InMemoryUserRepository:
    """Minimal structural implementation used to validate the protocol."""

    def __init__(self) -> None:
        self._users_by_id: dict[UserId, User] = {}
        self._users_by_username: dict[Username, User] = {}

    def get_by_id(self, user_id: UserId) -> User | None:
        return self._users_by_id.get(user_id)

    def get_by_username(self, username: Username) -> User | None:
        return self._users_by_username.get(username)

    def save(self, user: User) -> None:
        self._users_by_id[user.user_id] = user
        self._users_by_username[user.username] = user


class IncompleteRepository:
    """Object that intentionally does not satisfy the protocol."""

    def get_by_id(self, user_id: UserId) -> User | None:
        return None


def test_complete_structural_implementation_satisfies_protocol() -> None:
    repository = InMemoryUserRepository()

    assert isinstance(repository, UserRepository)


def test_incomplete_implementation_does_not_satisfy_protocol() -> None:
    repository = IncompleteRepository()

    assert not isinstance(repository, UserRepository)


def test_protocol_exposes_get_by_id_operation() -> None:
    assert callable(getattr(UserRepository, "get_by_id"))


def test_protocol_exposes_get_by_username_operation() -> None:
    assert callable(getattr(UserRepository, "get_by_username"))


def test_protocol_exposes_save_operation() -> None:
    assert callable(getattr(UserRepository, "save"))


def test_protocol_does_not_define_infrastructure_operations() -> None:
    assert not hasattr(UserRepository, "commit")
    assert not hasattr(UserRepository, "rollback")
    assert not hasattr(UserRepository, "execute")
    assert not hasattr(UserRepository, "connect")


def test_protocol_does_not_define_unneeded_crud_operations() -> None:
    assert not hasattr(UserRepository, "delete")
    assert not hasattr(UserRepository, "list")
    assert not hasattr(UserRepository, "find_all")
