"""Excepciones de dominio y manejadores HTTP."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.responses import error_response

logger = logging.getLogger(__name__)


class ControlCenterError(Exception):
    """Excepción base controlada del EJTV Control Center."""

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
    return getattr(request.state, "request_id", None)


async def control_center_error_handler(
    request: Request,
    exc: ControlCenterError,
) -> JSONResponse:
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


async def http_error_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
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
