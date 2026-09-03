"""Punto de entrada del EJTV Control Center Backend."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request

from app.api.dependencies import (
    get_alarm_recovery_service,
    get_daily_alarm_continuity_service,
    get_daily_history_maintenance_runtime,
    get_evidence_reconciliation_service,
    get_capacity_service,
    get_node_registry,
    get_runtime_owner_lock,
    get_system_service,
    get_telemetry_observation_runtime,
    get_session_observation_runtime,
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
    initialize_noc_runtime_capacity,
    initialize_noc_runtime_info,
)
from app.noc.domain.node_instance import NodeInstanceId

settings = get_settings()
configure_logging(settings)


@asynccontextmanager
async def _owned_noc_runtime(
    *,
    node_id,
    node_instance_id: NodeInstanceId,
    registry,
) -> AsyncIterator[None]:
    """Run operational NOC work while ownership is held."""

    continuity_through = datetime.now(timezone.utc)

    get_daily_alarm_continuity_service().catch_up(
        node_id=node_id,
        instance_id=node_instance_id,
        through=continuity_through,
    )

    get_alarm_recovery_service().recover(
        node_id=node_id,
        instance_id=node_instance_id,
    )

    reconciliation_end = datetime.now(timezone.utc)

    get_evidence_reconciliation_service().reconcile_between(
        start=reconciliation_end - timedelta(hours=48),
        end=reconciliation_end,
        node_id=node_id,
        instance_id=node_instance_id,
    )

    get_daily_history_maintenance_runtime().catch_up_mature_days(
        node_id=node_id,
        instance_id=node_instance_id,
        through=reconciliation_end,
    )

    initialize_noc_runtime_info(
        registry
    )

    initialize_noc_runtime_capacity(
        registry=registry,
        system_service=get_system_service(),
        capacity_service=get_capacity_service(),
    )

    telemetry_task = asyncio.create_task(
        get_telemetry_observation_runtime().run_forever(
            node_id=node_id,
            instance_id=node_instance_id,
            interval_seconds=5.0,
        ),
        name="noc-telemetry-refresh",
    )

    session_observation_task = asyncio.create_task(
        get_session_observation_runtime().run_forever(
            node_id=node_id,
            instance_id=node_instance_id,
            interval_seconds=5.0,
        ),
        name="noc-session-observation",
    )

    daily_history_task = asyncio.create_task(
        get_daily_history_maintenance_runtime().run_forever(
            node_id=node_id,
            instance_id=node_instance_id,
        ),
        name="noc-daily-history-maintenance",
    )

    try:
        yield
    finally:
        telemetry_task.cancel()
        session_observation_task.cancel()
        daily_history_task.cancel()

        with suppress(asyncio.CancelledError):
            await telemetry_task

        with suppress(asyncio.CancelledError):
            await session_observation_task

        with suppress(asyncio.CancelledError):
            await daily_history_task


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await application_startup(settings)

    try:
        registry = get_node_registry()

        bootstrap_result = bootstrap_noc_runtime(
            registry
        )

        node_instance_id = NodeInstanceId(
            DEFAULT_INSTANCE_ID
        )

        runtime_owner_lock = get_runtime_owner_lock()

        with runtime_owner_lock.exclusive(
            node_id=bootstrap_result.node.node_id,
            instance_id=node_instance_id,
        ):
            async with _owned_noc_runtime(
                node_id=bootstrap_result.node.node_id,
                node_instance_id=node_instance_id,
                registry=registry,
            ):
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
