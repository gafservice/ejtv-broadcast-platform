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
from app.noc.domain.node_health_diagnostic import (
    NodeHealthDiagnostic,
)
from app.domain.system import (
    NetworkInterfaceInfo,
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
from app.noc.services.health_transition_event_service import (
    HealthTransitionEventService,
)
from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
)
from app.noc.services.network_health_aggregator import (
    NetworkHealthAggregator,
)
from app.noc.services.network_interface_effective_health_evaluator import (
    NetworkInterfaceEffectiveHealthEvaluator,
)
from app.noc.services.network_interface_health_evaluator import (
    NetworkInterfaceHealthEvaluator,
)
from app.noc.services.network_interface_health_stabilizer import (
    NetworkInterfaceHealthStabilizer,
)
from app.noc.services.node_subsystem_health_aggregator import (
    NodeSubsystemHealthAggregator,
)
from app.services.network_telemetry_service import (
    NetworkTelemetryService,
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
    health_diagnostic: NodeHealthDiagnostic

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
        health_transition_event_service: (
            HealthTransitionEventService | None
        ) = None,
        provider: SystemMetricsProvider | None = None,
        health_evaluator: HealthEvaluator | None = None,
        network_health_stabilizer: (
            NetworkInterfaceHealthStabilizer | None
        ) = None,
        network_policies: tuple[
            NetworkInterfacePolicy,
            ...,
        ] = (),
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
            health_transition_event_service is not None
            and not isinstance(
                health_transition_event_service,
                HealthTransitionEventService,
            )
        ):
            raise TypeError(
                "health_transition_event_service must be a "
                "HealthTransitionEventService or None"
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
            network_health_stabilizer is not None
            and not isinstance(
                network_health_stabilizer,
                NetworkInterfaceHealthStabilizer,
            )
        ):
            raise TypeError(
                "network_health_stabilizer must be a "
                "NetworkInterfaceHealthStabilizer or None"
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

        if not isinstance(network_policies, tuple):
            raise TypeError(
                "network_policies must be a tuple"
            )

        for policy in network_policies:
            if not isinstance(
                policy,
                NetworkInterfacePolicy,
            ):
                raise TypeError(
                    "network_policies must contain "
                    "NetworkInterfacePolicy objects"
                )

        policy_interfaces = tuple(
            policy.interface
            for policy in network_policies
        )

        if len(set(policy_interfaces)) != len(
            policy_interfaces
        ):
            raise ValueError(
                "network_policies must not contain "
                "duplicate interfaces"
            )

        self._system_service = system_service
        self._metric_service = metric_service
        self._health_service = health_service
        self._health_transition_event_service = (
            health_transition_event_service
        )
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
        self._network_telemetry_service = (
            NetworkTelemetryService()
        )
        self._network_health_evaluator = (
            NetworkInterfaceHealthEvaluator()
        )
        self._network_health_stabilizer = (
            network_health_stabilizer
            if network_health_stabilizer is not None
            else NetworkInterfaceHealthStabilizer()
        )
        self._network_effective_health_evaluator = (
            NetworkInterfaceEffectiveHealthEvaluator()
        )
        self._network_health_aggregator = (
            NetworkHealthAggregator()
        )
        self._node_health_aggregator = (
            NodeSubsystemHealthAggregator()
        )
        self._network_policies = {
            policy.interface: policy
            for policy in network_policies
        }
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
    def health_transition_event_service(
        self,
    ) -> HealthTransitionEventService | None:
        return self._health_transition_event_service

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

        interface_infos = (
            self._system_service
            .get_network_interface_infos()
        )

        return self.refresh_from_capture(
            node_id=node_id,
            instance_id=instance_id,
            resources=resources,
            interface_infos=interface_infos,
        )

    def refresh_from_capture(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        resources: SystemResources,
        interface_infos: tuple[
            NetworkInterfaceInfo,
            ...,
        ],
    ) -> TelemetryRefreshResult:
        """Process and publish an already captured system state."""

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

        if not isinstance(
            resources,
            SystemResources,
        ):
            raise TypeError(
                "resources must be a SystemResources"
            )

        if not isinstance(
            interface_infos,
            tuple,
        ):
            raise TypeError(
                "interface_infos must be a tuple"
            )

        if not all(
            isinstance(
                interface_info,
                NetworkInterfaceInfo,
            )
            for interface_info in interface_infos
        ):
            raise TypeError(
                "interface_infos must contain "
                "NetworkInterfaceInfo objects"
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

        system_health = (
            self._health_evaluator.evaluate(
                current_metrics
            )
        )

        network_telemetry = (
            self._network_telemetry_service.build(
                previous=self._previous_resources,
                current=resources,
                interface_infos=interface_infos,
            )
        )

        effective_interface_health = []

        for telemetry in network_telemetry:
            observed = (
                self._network_health_evaluator.evaluate(
                    telemetry
                )
            )

            policy = self._network_policies.get(
                telemetry.interface
            )

            if policy is None:
                effective = observed
            else:
                effective = (
                    self._network_effective_health_evaluator
                    .evaluate(
                        observed,
                        policy,
                    )
                )

            stabilized = (
                self._network_health_stabilizer.stabilize(
                    effective
                )
            )

            effective_interface_health.append(
                stabilized
            )

        network_health = (
            self._network_health_aggregator.aggregate(
                tuple(effective_interface_health)
            )
        )

        previous_health = self._health_service.current(
            node_id,
            instance_id,
        )

        health = (
            self._node_health_aggregator.aggregate(
                (
                    system_health,
                    network_health,
                )
            )
        )

        health_diagnostic = NodeHealthDiagnostic(
            captured_at=resources.captured_at,
            health=health,
            system_health=system_health,
            network_health=network_health,
            network_interfaces=tuple(
                effective_interface_health
            ),
        )

        if self._health_transition_event_service is not None:
            self._health_transition_event_service.process(
                node_id=node_id,
                instance_id=instance_id,
                previous=previous_health,
                current=health,
                timestamp=resources.captured_at,
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
            health_diagnostic=health_diagnostic,
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
