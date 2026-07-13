"""Constructores de respuestas uniformes para la API."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_timestamp() -> str:
    """Genera una fecha UTC en formato ISO 8601."""

    return datetime.now(timezone.utc).isoformat()


def success_response(
    *,
    data: Any = None,
    message: str = "",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Construye una respuesta exitosa estándar."""

    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": utc_timestamp(),
        "request_id": request_id or str(uuid4()),
    }


def error_response(
    *,
    message: str,
    error_code: str,
    details: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Construye una respuesta de error estándar."""

    return {
        "success": False,
        "data": None,
        "message": message,
        "error": {
            "code": error_code,
            "details": details,
        },
        "timestamp": utc_timestamp(),
        "request_id": request_id or str(uuid4()),
    }
