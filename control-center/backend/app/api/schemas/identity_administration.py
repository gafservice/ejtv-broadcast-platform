"""Schemas HTTP para la administración de Identity."""

from pydantic import BaseModel, Field

from app.domain.identity.enums import UserStatus


class CreateUserRequest(BaseModel):
    """Datos requeridos para crear un usuario."""

    username: str = Field(
        min_length=3,
        max_length=64,
        description="Nombre único del usuario.",
        examples=["noc_operator"],
    )

    email: str = Field(
        min_length=3,
        max_length=254,
        description="Correo electrónico único del usuario.",
        examples=["operator@example.com"],
    )

    password: str = Field(
        min_length=1,
        max_length=72,
        description="Contraseña inicial del usuario.",
        examples=["change-this-password"],
    )


class UserResponse(BaseModel):
    """Representación pública de un usuario de Identity."""

    user_id: str
    username: str
    email: str
    status: UserStatus
    roles: list[str]


class UserListResponse(BaseModel):
    """Colección de usuarios administrados."""

    users: list[UserResponse]
    total: int


class ChangeUserStatusRequest(BaseModel):
    """Nuevo estado operativo de un usuario."""

    status: UserStatus


class ChangeUserPasswordRequest(BaseModel):
    """Nueva contraseña administrativa de un usuario."""

    password: str = Field(
        min_length=1,
        max_length=72,
        description="Nueva contraseña del usuario.",
        examples=["new-secure-password"],
    )


class AssignUserRoleRequest(BaseModel):
    """Rol canónico que será asignado a un usuario."""

    role_name: str = Field(
        min_length=3,
        max_length=64,
        description="Nombre del rol oficial.",
        examples=["operator"],
    )


class RoleResponse(BaseModel):
    """Representación pública de un rol canónico."""

    name: str
    permissions: list[str]


class RoleListResponse(BaseModel):
    """Colección de roles oficiales."""

    roles: list[RoleResponse]
    total: int


class PermissionResponse(BaseModel):
    """Representación pública de un permiso canónico."""

    name: str


class PermissionListResponse(BaseModel):
    """Colección de permisos oficiales."""

    permissions: list[PermissionResponse]
    total: int

