"""Domain protocols for identity and access management."""

from .password_hasher import PasswordHasher
from .user_repository import UserRepository

__all__ = [
    "PasswordHasher",
    "UserRepository",
]
