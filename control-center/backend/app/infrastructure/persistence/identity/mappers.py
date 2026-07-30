"""Mapping from identity ORM models to domain entities."""

from __future__ import annotations

from app.domain.identity.entities import (
    Permission,
    Role,
    User,
)
from app.domain.identity.enums import UserStatus
from app.domain.identity.value_objects import (
    Email,
    PasswordHash,
    PermissionName,
    RoleName,
    UserId,
    Username,
)
from app.infrastructure.persistence.identity.models import (
    UserModel,
)


def user_model_to_domain(
    model: UserModel,
) -> User:
    """Reconstruct a domain User from an ORM model."""
    if not isinstance(model, UserModel):
        raise TypeError("model must be a UserModel")

    roles = frozenset(
        Role(
            name=RoleName(role_model.name),
            permissions=frozenset(
                Permission(
                    name=PermissionName(
                        permission_model.name
                    )
                )
                for permission_model
                in role_model.permissions
            ),
        )
        for role_model in model.roles
    )

    return User(
        id=UserId.from_string(model.id),
        username=Username(model.username),
        email=Email(model.email),
        password_hash=PasswordHash(
            model.password_hash
        ),
        roles=roles,
        status=UserStatus(model.status),
    )
