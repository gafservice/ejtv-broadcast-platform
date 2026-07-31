"""Domain contract for user persistence."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.identity.entities import User
from app.domain.identity.value_objects import (
    Email,
    UserId,
    Username,
)


@runtime_checkable
class UserRepository(Protocol):
    """Persistence contract required by identity use cases.

    The domain defines only the operations it needs. Concrete storage
    mechanisms belong to the infrastructure layer.
    """

    def get_by_id(self, user_id: UserId) -> User | None:
        """Return the user identified by ``user_id``, if it exists."""
        ...

    def get_by_username(self, username: Username) -> User | None:
        """Return the user identified by ``username``, if it exists."""
        ...

    def get_by_email(self, email: Email) -> User | None:
        """Return the user identified by ``email``, if it exists."""
        ...

    def list(self) -> tuple[User, ...]:
        """Return all users ordered deterministically."""
        ...

    def save(self, user: User) -> None:
        """Persist the current state of ``user``."""
        ...
