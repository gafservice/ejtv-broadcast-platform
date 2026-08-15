"""Punto de entrada del EJTV Control Center Backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.dependencies import get_node_registry
from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import request_id_middleware
from app.core.responses import success_response
from app.core.shutdown import application_shutdown
from app.core.startup import application_startup
from app.core.version import APP_VERSION
from app.noc.bootstrap import (
    bootstrap_noc_runtime,
    initialize_noc_runtime_info,
)

settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await application_startup(settings)

    bootstrap_noc_runtime(
        get_node_registry()
    )

    initialize_noc_runtime_info(
        get_node_registry()
    )

    try:
        yield
    finally:
        await application_shutdown()


def create_application() -> FastAPI:
    """Construye y configura la aplicación FastAPI."""

    application = FastAPI(
        title=settings.app_name,
        version=APP_VERSION,
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.middleware("http")(request_id_middleware)
    application.include_router(api_router)

    register_exception_handlers(application)

    return application


app = create_application()


@app.get("/", tags=["Root"])
def root(request: Request) -> dict[str, object]:
    """Presenta información básica de la aplicación."""

    return success_response(
        data={
            "application": settings.app_name,
            "status": "running",
            "version": APP_VERSION,
            "documentation": "/docs",
        },
        message="EJTV Control Center Backend disponible.",
        request_id=request.state.request_id,
    )
