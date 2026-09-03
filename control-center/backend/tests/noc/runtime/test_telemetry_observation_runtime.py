"""Tests for the telemetry observation runtime."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.noc.current_state.repository import (
    NodeHealthDiagnosticRepository,
)
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.telemetry_observation_runtime import (
    TelemetryObservationRuntime,
)
from app.noc.runtime.telemetry_refresh import (
    TelemetryRefreshResult,
    TelemetryRefreshService,
)


TIMESTAMP = datetime(
    2026,
    9,
    3,
    12,
    0,
    tzinfo=UTC,
)

NODE_ID = NodeId.create(
    id="noc-core",
    name="noc",
    display_name="NOC Core",
)

INSTANCE_ID = NodeInstanceId(
    "noc-primary"
)


class FakeDiagnosticRepository:
    """Minimal current-state repository for runtime tests."""

    def __init__(self) -> None:
        self.save = Mock()

    def latest(
        self,
        *,
        node_id,
        instance_id,
    ):
        return None


def diagnostic() -> NodeHealthDiagnostic:
    health = NodeHealth(
        NodeHealthState.HEALTHY
    )

    return NodeHealthDiagnostic(
        captured_at=TIMESTAMP,
        health=health,
        system_health=health,
        network_health=health,
    )


def refresh_result() -> TelemetryRefreshResult:
    return TelemetryRefreshResult(
        captured_at=TIMESTAMP,
        samples=(),
        receipts=(),
        health_diagnostic=diagnostic(),
    )


def build_runtime():
    telemetry_refresh_service = object.__new__(
        TelemetryRefreshService
    )
    telemetry_refresh_service.refresh_once = Mock(
        return_value=refresh_result()
    )

    repository = FakeDiagnosticRepository()

    assert isinstance(
        repository,
        NodeHealthDiagnosticRepository,
    )

    runtime = TelemetryObservationRuntime(
        telemetry_refresh_service=(
            telemetry_refresh_service
        ),
        health_diagnostic_repository=repository,
    )

    return (
        runtime,
        telemetry_refresh_service,
        repository,
    )


def test_run_once_refreshes_and_publishes_diagnostic() -> None:
    (
        runtime,
        telemetry_refresh_service,
        repository,
    ) = build_runtime()

    result = runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    telemetry_refresh_service.refresh_once.assert_called_once_with(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    repository.save.assert_called_once_with(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        diagnostic=result.health_diagnostic,
    )

    assert isinstance(
        result,
        TelemetryRefreshResult,
    )


def test_run_once_returns_original_refresh_result() -> None:
    (
        runtime,
        telemetry_refresh_service,
        _,
    ) = build_runtime()

    expected = (
        telemetry_refresh_service
        .refresh_once.return_value
    )

    result = runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    assert result is expected


def test_failed_refresh_does_not_publish_diagnostic() -> None:
    (
        runtime,
        telemetry_refresh_service,
        repository,
    ) = build_runtime()

    telemetry_refresh_service.refresh_once.side_effect = (
        RuntimeError("refresh failure")
    )

    with pytest.raises(
        RuntimeError,
        match="refresh failure",
    ):
        runtime.run_once(
            node_id=NODE_ID,
            instance_id=INSTANCE_ID,
        )

    repository.save.assert_not_called()


def test_repository_failure_is_propagated() -> None:
    (
        runtime,
        _,
        repository,
    ) = build_runtime()

    repository.save.side_effect = RuntimeError(
        "repository failure"
    )

    with pytest.raises(
        RuntimeError,
        match="repository failure",
    ):
        runtime.run_once(
            node_id=NODE_ID,
            instance_id=INSTANCE_ID,
        )


def test_run_forever_rejects_non_positive_interval() -> None:
    import asyncio

    runtime, _, _ = build_runtime()

    with pytest.raises(
        ValueError,
        match="interval_seconds must be greater than zero",
    ):
        asyncio.run(
            runtime.run_forever(
                node_id=NODE_ID,
                instance_id=INSTANCE_ID,
                interval_seconds=0,
            )
        )


def test_run_forever_rejects_boolean_interval() -> None:
    import asyncio

    runtime, _, _ = build_runtime()

    with pytest.raises(
        TypeError,
        match="interval_seconds must be a number",
    ):
        asyncio.run(
            runtime.run_forever(
                node_id=NODE_ID,
                instance_id=INSTANCE_ID,
                interval_seconds=True,
            )
        )
