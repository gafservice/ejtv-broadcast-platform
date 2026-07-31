"""Catálogo oficial de permisos y roles del dominio Identity."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.identity.value_objects import PermissionName, RoleName


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    """Define un rol reservado y sus permisos."""

    name: RoleName
    permissions: frozenset[PermissionName]


SYSTEM_READ = PermissionName("system.read")
SYSTEM_WRITE = PermissionName("system.write")

DASHBOARD_READ = PermissionName("dashboard.read")
DASHBOARD_WRITE = PermissionName("dashboard.write")

STREAMING_READ = PermissionName("streaming.read")
STREAMING_WRITE = PermissionName("streaming.write")

IDENTITY_READ = PermissionName("identity.read")
IDENTITY_WRITE = PermissionName("identity.write")

USERS_READ = PermissionName("users.read")
USERS_WRITE = PermissionName("users.write")
USERS_MANAGE = PermissionName("users.manage")

ROLES_READ = PermissionName("roles.read")
ROLES_WRITE = PermissionName("roles.write")

ALARMS_READ = PermissionName("alarms.read")
ALARMS_WRITE = PermissionName("alarms.write")


ALL_PERMISSIONS = frozenset(
    {
        SYSTEM_READ,
        SYSTEM_WRITE,
        DASHBOARD_READ,
        DASHBOARD_WRITE,
        STREAMING_READ,
        STREAMING_WRITE,
        IDENTITY_READ,
        IDENTITY_WRITE,
        USERS_READ,
        USERS_WRITE,
        USERS_MANAGE,
        ROLES_READ,
        ROLES_WRITE,
        ALARMS_READ,
        ALARMS_WRITE,
    }
)


ADMINISTRATOR_ROLE = RoleDefinition(
    name=RoleName("administrator"),
    permissions=ALL_PERMISSIONS,
)


OPERATOR_ROLE = RoleDefinition(
    name=RoleName("operator"),
    permissions=frozenset(
        {
            SYSTEM_READ,
            DASHBOARD_READ,
            STREAMING_READ,
            STREAMING_WRITE,
            ALARMS_READ,
            ALARMS_WRITE,
        }
    ),
)


VIEWER_ROLE = RoleDefinition(
    name=RoleName("viewer"),
    permissions=frozenset(
        {
            SYSTEM_READ,
            DASHBOARD_READ,
            STREAMING_READ,
            ALARMS_READ,
        }
    ),
)


DEFAULT_ROLES = frozenset(
    {
        ADMINISTRATOR_ROLE,
        OPERATOR_ROLE,
        VIEWER_ROLE,
    }
)


def get_role_definition(
    role_name: RoleName,
) -> RoleDefinition | None:
    """Return a reserved role definition by name."""

    if not isinstance(role_name, RoleName):
        raise TypeError("role_name must be a RoleName")

    return next(
        (
            role
            for role in DEFAULT_ROLES
            if role.name == role_name
        ),
        None,
    )

