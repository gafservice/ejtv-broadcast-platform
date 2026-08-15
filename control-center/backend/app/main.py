"""Punto de entrada del EJTV Control Center Backend."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request

from app.api.dependencies import (
    get_node_registry,
    get_telemetry_refresh_service,
)
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
    DEFAULT_INSTANCE_ID,
    bootstrap_noc_runtime,
    initialize_noc_runtime_info,
)
from app.noc.domain.node_instance import NodeInstanceId

settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await application_startup(settings)

    registry = get_node_registry()

    bootstrap_result = bootstrap_noc_runtime(
        registry
    )

    initialize_noc_runtime_info(
        registry
    )

    telemetry_task = asyncio.create_task(
        get_telemetry_refresh_service().run_forever(
            node_id=bootstrap_result.node.node_id,
            instance_id=NodeInstanceId(
                DEFAULT_INSTANCE_ID
            ),
            interval_seconds=5.0,
        ),
        name="noc-telemetry-refresh",
    )

    try:
        yield
    finally:
        telemetry_task.cancel()

        with suppress(asyncio.CancelledError):
            await telemetry_task

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
