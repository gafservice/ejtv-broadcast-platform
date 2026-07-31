"""Schemas HTTP para autenticación."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credenciales recibidas para iniciar sesión."""

    username: str = Field(
        min_length=3,
        max_length=64,
        description="Nombre de usuario.",
        examples=["administrator"],
    )
    password: str = Field(
        min_length=1,
        max_length=256,
        description="Contraseña del usuario.",
        examples=["change-me"],
    )


class LoginResponse(BaseModel):
    """Datos devueltos después de una autenticación exitosa."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class CurrentIdentityResponse(BaseModel):
    """Identidad autenticada representada en la API."""

    user_id: str
    username: str
    roles: list[str]
    permissions: list[str]
