"""Middleware común de la aplicación."""

from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

from app.core.constants import HEADER_REQUEST_ID


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Asigna un identificador único a cada solicitud."""

    request_id = request.headers.get(HEADER_REQUEST_ID) or str(uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers[HEADER_REQUEST_ID] = request_id

    return response
