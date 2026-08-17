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
from app.domain.system import (
    NetworkRateCalculator,
    SystemResources,
)
from app.noc.infrastructure.network_rate_metrics_provider import (
    NetworkRateMetricsProvider,
)
from app.noc.infrastructure.system_metrics_provider import (
    SystemMetricsProvider,
)
from app.noc.services.health_evaluator import (
    HealthEvaluator,
)
from app.noc.services.health_service import (
    HealthService,
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
        health_service: HealthService,
        provider: SystemMetricsProvider | None = None,
        health_evaluator: HealthEvaluator | None = None,
    ) -> None:
        if not isinstance(system_service, SystemService):
            raise TypeError(
                "system_service must be a SystemService"
            )

        if not isinstance(metric_service, MetricService):
            raise TypeError(
                "metric_service must be a MetricService"
            )

        if not isinstance(
            health_service,
            HealthService,
        ):
            raise TypeError(
                "health_service must be a HealthService"
            )

        if (
            health_evaluator is not None
            and not isinstance(
                health_evaluator,
                HealthEvaluator,
            )
        ):
            raise TypeError(
                "health_evaluator must be a HealthEvaluator or None"
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
        self._health_service = health_service
        self._health_evaluator = (
            health_evaluator
            or HealthEvaluator()
        )
        self._provider = (
            provider
            or SystemMetricsProvider()
        )
        self._network_rate_calculator = (
            NetworkRateCalculator()
        )
        self._network_rate_provider = (
            NetworkRateMetricsProvider()
        )
        self._previous_resources: SystemResources | None = None

    @property
    def system_service(self) -> SystemService:
        return self._system_service

    @property
    def metric_service(self) -> MetricService:
        return self._metric_service

    @property
    def provider(self) -> SystemMetricsProvider:
        return self._provider

    @property
    def health_service(self) -> HealthService:
        return self._health_service

    @property
    def health_evaluator(self) -> HealthEvaluator:
        return self._health_evaluator

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

        base_samples = self._provider.collect(
            resources
        )

        network_rate = (
            self._network_rate_calculator.compare(
                self._previous_resources,
                resources,
            )
        )

        rate_samples = (
            self._network_rate_provider.collect(
                network_rate
            )
        )

        samples = (
            base_samples
            + rate_samples
        )

        receipts = tuple(
            self._metric_service.receive(
                node_id,
                instance_id,
                sample,
            )
            for sample in samples
        )

        current_metrics = (
            self._metric_service.current(
                node_id,
                instance_id,
            )
        )

        health = (
            self._health_evaluator.evaluate(
                current_metrics
            )
        )

        self._health_service.publish(
            node_id,
            instance_id,
            health,
        )

        self._previous_resources = resources

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
