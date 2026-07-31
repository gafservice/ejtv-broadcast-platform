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
