"""Runtime telemetry refresh coordination for the NOC.

ENG-013B — Node SDK

TelemetryRefreshService performs one deterministic refresh cycle:

SystemService
    -> SystemResources
    -> SystemMetricsProvider
    -> MetricService

Scheduling and background execution belong to another layer.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_metric import MetricSample
from app.noc.infrastructure.system_metrics_provider import (
    SystemMetricsProvider,
)
from app.noc.services.metric_service import (
    MetricReceipt,
    MetricService,
)
from app.services.system_service import SystemService


@dataclass(frozen=True, slots=True)
class TelemetryRefreshResult:
    """Result of one telemetry refresh cycle."""

    captured_at: datetime
    samples: tuple[MetricSample, ...]
    receipts: tuple[MetricReceipt, ...]

    @property
    def metric_count(self) -> int:
        return len(self.samples)


class TelemetryRefreshService:
    """Refresh current NOC metrics from SystemService."""

    def __init__(
        self,
        *,
        system_service: SystemService,
        metric_service: MetricService,
        provider: SystemMetricsProvider | None = None,
    ) -> None:
        if not isinstance(system_service, SystemService):
            raise TypeError(
                "system_service must be a SystemService"
            )

        if not isinstance(metric_service, MetricService):
            raise TypeError(
                "metric_service must be a MetricService"
            )

        if (
            provider is not None
            and not isinstance(
                provider,
                SystemMetricsProvider,
            )
        ):
            raise TypeError(
                "provider must be a SystemMetricsProvider or None"
            )

        self._system_service = system_service
        self._metric_service = metric_service
        self._provider = (
            provider
            or SystemMetricsProvider()
        )

    @property
    def system_service(self) -> SystemService:
        return self._system_service

    @property
    def metric_service(self) -> MetricService:
        return self._metric_service

    @property
    def provider(self) -> SystemMetricsProvider:
        return self._provider

    def refresh_once(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> TelemetryRefreshResult:
        """Capture and publish one current system telemetry sample set."""

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

        resources = (
            self._system_service
            .get_system_resources()
        )

        samples = self._provider.collect(
            resources
        )

        receipts = tuple(
            self._metric_service.receive(
                node_id,
                instance_id,
                sample,
            )
            for sample in samples
        )

        return TelemetryRefreshResult(
            captured_at=resources.captured_at,
            samples=samples,
            receipts=receipts,
        )


    async def run_forever(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        interval_seconds: float,
    ) -> None:
        """Refresh telemetry periodically until the task is cancelled."""

        if isinstance(interval_seconds, bool) or not isinstance(
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
            self.refresh_once(
                node_id=node_id,
                instance_id=instance_id,
            )

            await asyncio.sleep(
                interval
            )
