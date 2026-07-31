"""Excepciones controladas y manejadores HTTP globales."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.responses import error_response
from app.domain.identity.exceptions import (
    InvalidCredentials,
    PermissionDenied,
    UserDisabled,
    UserLocked,
)

logger = logging.getLogger(__name__)


class ControlCenterError(Exception):
    """Excepción base controlada del Control Center."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str = "CONTROL_CENTER_ERROR",
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


class ResourceNotFoundError(ControlCenterError):
    """Recurso solicitado no encontrado."""

    def __init__(
        self,
        message: str = "El recurso solicitado no existe.",
        *,
        details: Any = None,
    ) -> None:
        super().__init__(
            message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
        )


class OperationNotAllowedError(ControlCenterError):
    """Operación no autorizada por las reglas de negocio."""

    def __init__(
        self,
        message: str = "La operación solicitada no está permitida.",
        *,
        details: Any = None,
    ) -> None:
        super().__init__(
            message,
            status_code=409,
            error_code="OPERATION_NOT_ALLOWED",
            details=details,
        )


def _request_id(request: Request) -> str | None:
    """Obtiene el identificador de la solicitud actual."""

    return getattr(request.state, "request_id", None)


async def control_center_error_handler(
    request: Request,
    exc: ControlCenterError,
) -> JSONResponse:
    """Maneja errores controlados de la aplicación."""

    logger.warning(
        "Error controlado: %s",
        exc.message,
        extra={"request_id": _request_id(request)},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
            request_id=_request_id(request),
        ),
    )


async def invalid_credentials_handler(
    request: Request,
    _: InvalidCredentials,
) -> JSONResponse:
    """Traduce credenciales inválidas a HTTP 401."""

    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
        content=error_response(
            message="Las credenciales proporcionadas no son válidas.",
            error_code="INVALID_CREDENTIALS",
            request_id=_request_id(request),
        ),
    )


async def permission_denied_handler(
    request: Request,
    _: PermissionDenied,
) -> JSONResponse:
    """Traduce la ausencia de permisos a HTTP 403."""

    return JSONResponse(
        status_code=403,
        content=error_response(
            message=(
                "La identidad autenticada no posee el permiso "
                "requerido."
            ),
            error_code="PERMISSION_DENIED",
            request_id=_request_id(request),
        ),
    )


async def user_disabled_handler(
    request: Request,
    _: UserDisabled,
) -> JSONResponse:
    """Traduce un usuario deshabilitado a HTTP 403."""

    return JSONResponse(
        status_code=403,
        content=error_response(
            message="La cuenta de usuario está deshabilitada.",
            error_code="USER_DISABLED",
            request_id=_request_id(request),
        ),
    )


async def user_locked_handler(
    request: Request,
    _: UserLocked,
) -> JSONResponse:
    """Traduce un usuario bloqueado a HTTP 423."""

    return JSONResponse(
        status_code=423,
        content=error_response(
            message="La cuenta de usuario está bloqueada.",
            error_code="USER_LOCKED",
            request_id=_request_id(request),
        ),
    )


async def http_error_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Maneja excepciones HTTP de Starlette y FastAPI."""

    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=error_response(
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            request_id=_request_id(request),
        ),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Maneja errores de validación de solicitudes."""

    return JSONResponse(
        status_code=422,
        content=error_response(
            message="La solicitud contiene datos inválidos.",
            error_code="VALIDATION_ERROR",
            details=exc.errors(),
            request_id=_request_id(request),
        ),
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Maneja errores inesperados sin exponer detalles internos."""

    logger.exception(
        "Error inesperado durante la solicitud.",
        extra={"request_id": _request_id(request)},
    )

    return JSONResponse(
        status_code=500,
        content=error_response(
            message="Ocurrió un error interno en el servidor.",
            error_code="INTERNAL_SERVER_ERROR",
            request_id=_request_id(request),
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los manejadores globales de excepción."""

    app.add_exception_handler(
        ControlCenterError,
        control_center_error_handler,
    )
    app.add_exception_handler(
        InvalidCredentials,
        invalid_credentials_handler,
    )
    app.add_exception_handler(
        PermissionDenied,
        permission_denied_handler,
    )
    app.add_exception_handler(
        UserDisabled,
        user_disabled_handler,
    )
    app.add_exception_handler(
        UserLocked,
        user_locked_handler,
    )
    app.add_exception_handler(
        StarletteHTTPException,
        http_error_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,
    )
    app.add_exception_handler(
        Exception,
        unexpected_error_handler,
    )
