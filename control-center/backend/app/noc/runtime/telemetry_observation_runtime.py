"""Operational runtime coordination for system telemetry observation.

ENG-013B — Node SDK

TelemetryObservationRuntime coordinates one telemetry observation cycle.

It delegates telemetry capture and health evaluation to
TelemetryRefreshService, then publishes the resulting
NodeHealthDiagnostic to shared current-state storage.

The runtime owns coordination only. It does not implement telemetry
evaluation, current-state serialization or SQLite persistence.
"""

from __future__ import annotations

import asyncio

from app.noc.current_state.repository import (
    NodeHealthDiagnosticRepository,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.runtime.telemetry_refresh import (
    TelemetryRefreshResult,
    TelemetryRefreshService,
)


class TelemetryObservationRuntime:
    """Coordinate telemetry refresh and shared diagnostic publication."""

    def __init__(
        self,
        *,
        telemetry_refresh_service: TelemetryRefreshService,
        health_diagnostic_repository: NodeHealthDiagnosticRepository,
    ) -> None:
        if not isinstance(
            telemetry_refresh_service,
            TelemetryRefreshService,
        ):
            raise TypeError(
                "telemetry_refresh_service must be a "
                "TelemetryRefreshService"
            )

        if not isinstance(
            health_diagnostic_repository,
            NodeHealthDiagnosticRepository,
        ):
            raise TypeError(
                "health_diagnostic_repository must satisfy "
                "NodeHealthDiagnosticRepository"
            )

        self._telemetry_refresh_service = (
            telemetry_refresh_service
        )
        self._health_diagnostic_repository = (
            health_diagnostic_repository
        )

    @property
    def telemetry_refresh_service(
        self,
    ) -> TelemetryRefreshService:
        return self._telemetry_refresh_service

    @property
    def health_diagnostic_repository(
        self,
    ) -> NodeHealthDiagnosticRepository:
        return self._health_diagnostic_repository

    def run_once(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> TelemetryRefreshResult:
        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        result = (
            self._telemetry_refresh_service.refresh_once(
                node_id=node_id,
                instance_id=instance_id,
            )
        )

        self._health_diagnostic_repository.save(
            node_id=node_id,
            instance_id=instance_id,
            diagnostic=result.health_diagnostic,
        )

        return result

    async def run_forever(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        interval_seconds: float,
    ) -> None:
        if isinstance(
            interval_seconds,
            bool,
        ) or not isinstance(
            interval_seconds,
            (int, float),
        ):
            raise TypeError(
                "interval_seconds must be a number"
            )

        interval = float(interval_seconds)

        if interval <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        while True:
            self.run_once(
                node_id=node_id,
                instance_id=instance_id,
            )

            await asyncio.sleep(interval)
