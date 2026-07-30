"""Endpoints de autenticación."""

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_authentication_service
from app.api.schemas.authentication import (
    LoginRequest,
    LoginResponse,
)
from app.core.config import get_settings
from app.core.responses import success_response
from app.services.authentication_service import AuthenticationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(
    credentials: LoginRequest,
    request: Request,
    service: AuthenticationService = Depends(
        get_authentication_service
    ),
) -> dict[str, object]:
    """Autentica un usuario y emite un token JWT."""

    token = service.authenticate(
        username=credentials.username,
        password=credentials.password,
    )

    settings = get_settings()

    response = LoginResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=settings.jwt_expiration_seconds,
    )

    return success_response(
        data=response.model_dump(),
        message="Autenticación completada correctamente.",
        request_id=request.state.request_id,
    )
