"""Tests for TelemetryRefreshService."""

from datetime import datetime, timedelta, timezone

import pytest

from app.adapters.base.system_adapter import SystemAdapter
from app.domain.system import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
    NetworkInfo,
    NetworkInterfaceInfo,
    NetworkInterfaceType,
    SystemResources,
    UptimeInfo,
)
from app.noc.domain.node import Node
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_health import (
    NodeHealth,
    NodeHealthState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.infrastructure.memory_repository import (
    InMemoryNodeRepository,
)
from app.noc.registry.registry import NodeRegistry
from app.noc.runtime.telemetry_refresh import (
    TelemetryRefreshResult,
    TelemetryRefreshService,
)
from app.noc.services.event_service import EventService
from app.noc.services.health_transition_event_service import (
    HealthTransitionEventService,
)
from app.noc.services.health_service import (
    HealthService,
)
from app.noc.services.metric_service import (
    MetricDisposition,
    MetricService,
)
from app.noc.services.snapshot_service import (
    SnapshotService,
)
from app.services.system_service import SystemService


CAPTURED_AT = datetime(
    2026,
    8,
    15,
    23,
    0,
    tzinfo=timezone.utc,
)


class FakeSystemAdapter(SystemAdapter):
    def hostname(self) -> str:
        return "ejtv-test"

    def operating_system(self) -> str:
        return "Test Linux"

    def kernel(self) -> str:
        return "test-kernel"

    def cpu_info(self) -> CPUInfo:
        return CPUInfo(
            usage_percent=20.0,
            logical_cores=4,
            physical_cores=2,
            frequency_mhz=2500.0,
            per_core_usage_percent=(
                10.0,
                20.0,
                30.0,
                20.0,
            ),
        )

    def memory_info(self) -> MemoryInfo:
        return MemoryInfo(
            total_bytes=8_000,
            available_bytes=5_000,
            used_bytes=3_000,
            usage_percent=37.5,
        )

    def disk_info(self) -> DiskInfo:
        return DiskInfo(
            total_bytes=100_000,
            used_bytes=25_000,
            free_bytes=75_000,
            usage_percent=25.0,
        )

    def network_info(
        self,
        interface: str,
    ) -> NetworkInfo:
        return NetworkInfo(
            interface=interface,
            bytes_sent=2_000,
            bytes_received=3_000,
            packets_sent=20,
            packets_received=30,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        )

    def network_interfaces(self) -> tuple[NetworkInfo, ...]:
        """Retorna las interfaces disponibles del adapter falso."""

        return (
            self.network_info("ens2f0"),
        )

    def network_interface_infos(
        self,
    ) -> tuple[NetworkInterfaceInfo, ...]:
        """Retorna identidad y estado de las interfaces."""

        return (
            NetworkInterfaceInfo(
                interface="ens2f0",
                interface_type=NetworkInterfaceType.ETHERNET,
                is_up=True,
                carrier=True,
                mtu=1500,
                link_speed_mbps=100,
            ),
        )

    def uptime_info(self) -> UptimeInfo:
        return UptimeInfo(
            uptime_seconds=3600
        )

    def service_monitoring(self):
        raise NotImplementedError


class FixedSystemService(SystemService):
    """SystemService with deterministic captured_at for tests."""

    def get_system_resources(self) -> SystemResources:
        adapter = self._adapter

        return SystemResources(
            cpu=adapter.cpu_info(),
            memory=adapter.memory_info(),
            disk=adapter.disk_info(),
            network=adapter.network_info(
                "ens2f0"
            ),
            uptime=adapter.uptime_info(),
            captured_at=CAPTURED_AT,
        )


def make_context():
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    metric_service = MetricService(
        registry
    )

    health_service = HealthService(
        registry
    )

    system_service = FixedSystemService(
        FakeSystemAdapter()
    )

    refresh_service = TelemetryRefreshService(
        system_service=system_service,
        metric_service=metric_service,
        health_service=health_service,
    )

    return (
        registry,
        node,
        instance,
        metric_service,
        refresh_service,
    )


def test_service_requires_system_service() -> None:
    _, _, _, metric_service, _ = make_context()

    with pytest.raises(TypeError):
        TelemetryRefreshService(
            system_service=object(),  # type: ignore[arg-type]
            metric_service=metric_service,
        )


def test_service_requires_metric_service() -> None:
    system_service = FixedSystemService(
        FakeSystemAdapter()
    )

    with pytest.raises(TypeError):
        TelemetryRefreshService(
            system_service=system_service,
            metric_service=object(),  # type: ignore[arg-type]
        )


def test_refresh_requires_node_id() -> None:
    _, _, instance, _, service = make_context()

    with pytest.raises(TypeError):
        service.refresh_once(
            node_id="streaming-core",  # type: ignore[arg-type]
            instance_id=instance.instance_id,
        )


def test_refresh_requires_instance_id() -> None:
    _, node, _, _, service = make_context()

    with pytest.raises(TypeError):
        service.refresh_once(
            node_id=node.node_id,
            instance_id="streaming-primary",  # type: ignore[arg-type]
        )


def test_refresh_returns_result() -> None:
    _, node, instance, _, service = make_context()

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert isinstance(
        result,
        TelemetryRefreshResult,
    )

    assert result.captured_at == CAPTURED_AT


def test_refresh_publishes_base_metrics() -> None:
    _, node, instance, _, service = make_context()

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert result.metric_count == 13
    assert len(result.samples) == 13
    assert len(result.receipts) == 13


def test_first_refresh_dispositions() -> None:
    _, node, instance, _, service = make_context()

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert (
        result.receipts[0].disposition
        is MetricDisposition.FIRST
    )

    assert all(
        receipt.disposition
        in {
            MetricDisposition.FIRST,
            MetricDisposition.ADDED,
        }
        for receipt in result.receipts
    )


def test_refresh_updates_metric_service_state() -> None:
    (
        _,
        node,
        instance,
        metric_service,
        service,
    ) = make_context()

    service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    current = metric_service.current(
        node.node_id,
        instance.instance_id,
    )

    assert len(current.samples) == 13

    assert current.has_metric(
        "system.cpu.usage_percent"
    )

    assert current.has_metric(
        "system.memory.usage_percent"
    )

    assert current.has_metric(
        "system.disk.usage_percent"
    )

    assert current.has_metric(
        "system.network.rx_bytes"
    )

    assert current.has_metric(
        "system.network.tx_bytes"
    )

    assert current.has_metric(
        "system.uptime_seconds"
    )


def test_refresh_is_reflected_in_snapshot() -> None:
    (
        registry,
        node,
        instance,
        _,
        service,
    ) = make_context()

    service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    snapshot = SnapshotService(
        registry
    ).build(
        node.node_id,
        instance.instance_id,
    )

    assert snapshot.metric is not None
    assert len(snapshot.metric.samples) == 13


def test_result_uses_single_capture_timestamp() -> None:
    _, node, instance, _, service = make_context()

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert {
        sample.timestamp
        for sample in result.samples
    } == {
        CAPTURED_AT
    }


def test_second_refresh_replaces_existing_metrics() -> None:
    from datetime import timedelta

    (
        _,
        node,
        instance,
        metric_service,
        service,
    ) = make_context()

    first = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert first.metric_count == 13

    first_current = metric_service.current(
        node.node_id,
        instance.instance_id,
    )

    first_cpu = first_current.get(
        "system.cpu.usage_percent"
    )

    assert first_cpu is not None
    assert first_cpu.timestamp == CAPTURED_AT

    original_get = (
        service.system_service.get_system_resources
    )

    def newer_resources() -> SystemResources:
        resources = original_get()

        return SystemResources(
            cpu=CPUInfo(
                usage_percent=55.0,
                logical_cores=resources.cpu.logical_cores,
                physical_cores=resources.cpu.physical_cores,
                frequency_mhz=resources.cpu.frequency_mhz,
                per_core_usage_percent=(
                    50.0,
                    55.0,
                    60.0,
                    55.0,
                ),
            ),
            memory=resources.memory,
            disk=resources.disk,
            network=NetworkInfo(
                interface=resources.network.interface,
                bytes_sent=resources.network.bytes_sent + 1000,
                bytes_received=resources.network.bytes_received + 2000,
                packets_sent=resources.network.packets_sent + 10,
                packets_received=resources.network.packets_received + 20,
                errors_in=resources.network.errors_in,
                errors_out=resources.network.errors_out,
                dropped_in=resources.network.dropped_in,
                dropped_out=resources.network.dropped_out,
            ),
            uptime=UptimeInfo(
                uptime_seconds=resources.uptime.uptime_seconds + 5,
            ),
            captured_at=CAPTURED_AT + timedelta(seconds=5),
        )

    service.system_service.get_system_resources = newer_resources

    second = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert second.metric_count == 19

    dispositions = {
        receipt.sample.metric: receipt.disposition
        for receipt in second.receipts
    }

    assert dispositions[
        "system.network.rx_bps"
    ] is MetricDisposition.ADDED

    assert dispositions[
        "system.network.tx_bps"
    ] is MetricDisposition.ADDED

    assert all(
        dispositions[metric]
        is MetricDisposition.REPLACED
        for metric in {
            "system.cpu.usage_percent",
            "system.memory.usage_percent",
            "system.disk.usage_percent",
            "system.network.rx_bytes",
            "system.network.tx_bytes",
            "system.uptime_seconds",
        }
    )

    current = metric_service.current(
        node.node_id,
        instance.instance_id,
    )

    cpu = current.get(
        "system.cpu.usage_percent"
    )

    assert cpu is not None
    assert cpu.value == 55.0
    assert cpu.timestamp == (
        CAPTURED_AT + timedelta(seconds=5)
    )

    assert len(current.samples) == 19

    rx_bps = current.get(
        "system.network.rx_bps"
    )

    tx_bps = current.get(
        "system.network.tx_bps"
    )

    assert rx_bps is not None
    assert tx_bps is not None

    assert rx_bps.value == 3200.0
    assert tx_bps.value == 1600.0

    assert rx_bps.unit == "bps"
    assert tx_bps.unit == "bps"



def test_run_forever_rejects_invalid_interval() -> None:
    import asyncio

    _, node, instance, _, service = make_context()

    async def scenario() -> None:
        with pytest.raises(ValueError):
            await service.run_forever(
                node_id=node.node_id,
                instance_id=instance.instance_id,
                interval_seconds=0,
            )

    asyncio.run(
        scenario()
    )


def test_run_forever_rejects_invalid_interval_type() -> None:
    import asyncio

    _, node, instance, _, service = make_context()

    async def scenario() -> None:
        with pytest.raises(TypeError):
            await service.run_forever(
                node_id=node.node_id,
                instance_id=instance.instance_id,
                interval_seconds="5",  # type: ignore[arg-type]
            )

    asyncio.run(
        scenario()
    )


def test_run_forever_refreshes_until_cancelled() -> None:
    import asyncio
    from datetime import timedelta

    _, node, instance, metric_service, service = make_context()

    original_get = (
        service.system_service.get_system_resources
    )

    call_count = 0

    def advancing_resources() -> SystemResources:
        nonlocal call_count

        resources = original_get()

        captured_at = (
            resources.captured_at
            + timedelta(
                milliseconds=call_count * 20
            )
        )

        call_count += 1

        return SystemResources(
            cpu=resources.cpu,
            memory=resources.memory,
            disk=resources.disk,
            network=NetworkInfo(
                interface=resources.network.interface,
                bytes_sent=(
                    resources.network.bytes_sent
                    + call_count
                ),
                bytes_received=(
                    resources.network.bytes_received
                    + call_count
                ),
                packets_sent=resources.network.packets_sent,
                packets_received=resources.network.packets_received,
                errors_in=resources.network.errors_in,
                errors_out=resources.network.errors_out,
                dropped_in=resources.network.dropped_in,
                dropped_out=resources.network.dropped_out,
            ),
            uptime=UptimeInfo(
                uptime_seconds=(
                    resources.uptime.uptime_seconds
                    + call_count
                )
            ),
            captured_at=captured_at,
        )

    service.system_service.get_system_resources = (
        advancing_resources
    )

    async def scenario() -> None:
        task = asyncio.create_task(
            service.run_forever(
                node_id=node.node_id,
                instance_id=instance.instance_id,
                interval_seconds=0.01,
            )
        )

        await asyncio.sleep(0.04)

        task.cancel()

        with pytest.raises(
            asyncio.CancelledError
        ):
            await task

    asyncio.run(
        scenario()
    )

    current = metric_service.current(
        node.node_id,
        instance.instance_id,
    )

    assert len(current.samples) == 19

    assert current.has_metric(
        "system.network.rx_bps"
    )

    assert current.has_metric(
        "system.network.tx_bps"
    )

    assert call_count >= 2


def test_run_forever_propagates_cancellation() -> None:
    import asyncio

    _, node, instance, _, service = make_context()

    async def scenario() -> None:
        task = asyncio.create_task(
            service.run_forever(
                node_id=node.node_id,
                instance_id=instance.instance_id,
                interval_seconds=60.0,
            )
        )

        await asyncio.sleep(0)

        task.cancel()

        with pytest.raises(
            asyncio.CancelledError
        ):
            await task

    asyncio.run(
        scenario()
    )


def test_refresh_publishes_node_health() -> None:
    from app.noc.domain.node_health import (
        NodeHealth,
        NodeHealthState,
    )

    _, node, instance, _, service = make_context()

    service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert isinstance(
        instance.health,
        NodeHealth,
    )

    assert instance.health.state is (
        NodeHealthState.HEALTHY
    )


def test_refresh_health_uses_current_metrics() -> None:
    from app.noc.domain.node_health import (
        NodeHealthState,
    )

    _, node, instance, _, service = make_context()

    original_get = (
        service.system_service.get_system_resources
    )

    def critical_resources() -> SystemResources:
        resources = original_get()

        return SystemResources(
            cpu=CPUInfo(
                usage_percent=96.0,
                logical_cores=resources.cpu.logical_cores,
                physical_cores=resources.cpu.physical_cores,
                frequency_mhz=resources.cpu.frequency_mhz,
                per_core_usage_percent=(
                    96.0,
                    96.0,
                    96.0,
                    96.0,
                ),
            ),
            memory=resources.memory,
            disk=resources.disk,
            network=resources.network,
            uptime=resources.uptime,
            captured_at=resources.captured_at,
        )

    service.system_service.get_system_resources = (
        critical_resources
    )

    service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert instance.health is not None

    assert instance.health.state is (
        NodeHealthState.CRITICAL
    )


def test_second_refresh_publishes_network_quality_rates() -> None:
    from datetime import timedelta

    _, node, instance, metric_service, service = make_context()

    original_get = (
        service.system_service.get_system_resources
    )

    first_resources = original_get()

    call_count = 0

    def quality_resources() -> SystemResources:
        nonlocal call_count

        call_count += 1

        if call_count == 1:
            return first_resources

        return SystemResources(
            cpu=first_resources.cpu,
            memory=first_resources.memory,
            disk=first_resources.disk,
            network=NetworkInfo(
                interface=first_resources.network.interface,
                bytes_sent=(
                    first_resources.network.bytes_sent
                    + 1_000
                ),
                bytes_received=(
                    first_resources.network.bytes_received
                    + 2_000
                ),
                packets_sent=(
                    first_resources.network.packets_sent
                    + 10
                ),
                packets_received=(
                    first_resources.network.packets_received
                    + 20
                ),
                errors_in=5,
                errors_out=10,
                dropped_in=30,
                dropped_out=20,
            ),
            uptime=UptimeInfo(
                uptime_seconds=(
                    first_resources.uptime.uptime_seconds
                    + 5
                )
            ),
            captured_at=(
                first_resources.captured_at
                + timedelta(seconds=5)
            ),
        )

    service.system_service.get_system_resources = (
        quality_resources
    )

    service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    second = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert second.metric_count == 19

    current = metric_service.current(
        node.node_id,
        instance.instance_id,
    )

    expected = {
        "system.network.errors_in_per_second": 1.0,
        "system.network.errors_out_per_second": 2.0,
        "system.network.dropped_in_per_second": 6.0,
        "system.network.dropped_out_per_second": 4.0,
    }

    for name, value in expected.items():
        sample = current.get(name)

        assert sample is not None
        assert sample.value == value
        assert sample.unit == "count/s"


# ---------------------------------------------------------------------------
# Network policy -> effective network health -> integral NodeHealth
# ---------------------------------------------------------------------------

from app.noc.domain.network_interface_policy import (
    NetworkInterfacePolicy,
    NetworkInterfaceRole,
)
from app.noc.domain.node_health import NodeHealthState


class NetworkPolicySystemAdapter(FakeSystemAdapter):
    """Adapter determinista para validar política operacional de NIC."""

    def __init__(
        self,
        *,
        interface: str,
        is_up: bool,
        carrier: bool,
    ) -> None:
        self._interface = interface
        self._is_up = is_up
        self._carrier = carrier

    def network_info(
        self,
        interface: str,
    ) -> NetworkInfo:
        return NetworkInfo(
            interface=interface,
            bytes_sent=2_000,
            bytes_received=3_000,
            packets_sent=20,
            packets_received=30,
            errors_in=0,
            errors_out=0,
            dropped_in=0,
            dropped_out=0,
        )

    def network_interfaces(
        self,
    ) -> tuple[NetworkInfo, ...]:
        return (
            self.network_info(
                self._interface
            ),
        )

    def network_interface_infos(
        self,
    ) -> tuple[NetworkInterfaceInfo, ...]:
        return (
            NetworkInterfaceInfo(
                interface=self._interface,
                interface_type=NetworkInterfaceType.ETHERNET,
                is_up=self._is_up,
                carrier=self._carrier,
                mtu=1500,
                link_speed_mbps=(
                    1000
                    if self._carrier
                    else None
                ),
            ),
        )


class NetworkPolicySystemService(FixedSystemService):
    """SystemService determinista para una NIC bajo prueba."""

    def get_system_resources(
        self,
    ) -> SystemResources:
        adapter = self._adapter

        return SystemResources(
            cpu=adapter.cpu_info(),
            memory=adapter.memory_info(),
            disk=adapter.disk_info(),
            network=adapter.network_info(
                adapter._interface
            ),
            uptime=adapter.uptime_info(),
            captured_at=CAPTURED_AT,
        )


def make_network_policy_context(
    *,
    interface: str,
    role: NetworkInterfaceRole,
    expected_up: bool,
    critical: bool,
    is_up: bool,
    carrier: bool,
):
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    metric_service = MetricService(
        registry
    )

    health_service = HealthService(
        registry
    )

    system_service = NetworkPolicySystemService(
        NetworkPolicySystemAdapter(
            interface=interface,
            is_up=is_up,
            carrier=carrier,
        )
    )

    policy = NetworkInterfacePolicy(
        interface=interface,
        role=role,
        expected_up=expected_up,
        critical=critical,
    )

    refresh_service = TelemetryRefreshService(
        system_service=system_service,
        metric_service=metric_service,
        health_service=health_service,
        network_policies=(policy,),
    )

    return (
        node,
        instance,
        health_service,
        refresh_service,
    )


def test_optional_backup_down_does_not_degrade_node_health() -> None:
    (
        node,
        instance,
        health_service,
        service,
    ) = make_network_policy_context(
        interface="ens2f1",
        role=NetworkInterfaceRole.BACKUP,
        expected_up=False,
        critical=False,
        is_up=False,
        carrier=False,
    )

    service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    health = health_service.current(
        node.node_id,
        instance.instance_id,
    )

    assert health is not None
    assert health.state is NodeHealthState.HEALTHY


def test_required_critical_ingest_down_makes_node_health_critical() -> None:
    (
        node,
        instance,
        health_service,
        service,
    ) = make_network_policy_context(
        interface="enp9s0",
        role=NetworkInterfaceRole.INGEST,
        expected_up=True,
        critical=True,
        is_up=False,
        carrier=False,
    )

    service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    health = health_service.current(
        node.node_id,
        instance.instance_id,
    )

    assert health is not None
    assert health.state is NodeHealthState.CRITICAL


def test_refresh_returns_health_diagnostic() -> None:
    _, node, instance, _, service = make_context()

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    diagnostic = result.health_diagnostic

    assert diagnostic.captured_at == CAPTURED_AT
    assert diagnostic.health is not None
    assert diagnostic.system_health is not None
    assert diagnostic.network_health is not None
    assert diagnostic.interface_count == 1


def test_backup_down_diagnostic_preserves_effective_health() -> None:
    (
        node,
        instance,
        _,
        service,
    ) = make_network_policy_context(
        interface="ens2f1",
        role=NetworkInterfaceRole.BACKUP,
        expected_up=False,
        critical=False,
        is_up=False,
        carrier=False,
    )

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    diagnostic = result.health_diagnostic

    assert (
        diagnostic.health.state
        is NodeHealthState.HEALTHY
    )

    assert (
        diagnostic.network_health.state
        is NodeHealthState.HEALTHY
    )

    assert diagnostic.interface_count == 1

    interface = diagnostic.network_interfaces[0]

    assert interface.interface == "ens2f1"
    assert interface.state is NodeHealthState.HEALTHY
    assert (
        interface.reason
        == "Optional interface is not required to be operational"
    )


def test_ingest_down_diagnostic_explains_critical_health() -> None:
    (
        node,
        instance,
        _,
        service,
    ) = make_network_policy_context(
        interface="enp9s0",
        role=NetworkInterfaceRole.INGEST,
        expected_up=True,
        critical=True,
        is_up=False,
        carrier=False,
    )

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    diagnostic = result.health_diagnostic

    assert (
        diagnostic.health.state
        is NodeHealthState.CRITICAL
    )

    assert (
        diagnostic.network_health.state
        is NodeHealthState.CRITICAL
    )

    assert diagnostic.interface_count == 1

    interface = diagnostic.network_interfaces[0]

    assert interface.interface == "enp9s0"
    assert interface.state is NodeHealthState.CRITICAL
    assert (
        interface.reason
        == "Required critical interface is not operational"
    )


# ---------------------------------------------------------------------------
# Explicit capture processing boundary
# ---------------------------------------------------------------------------


def test_refresh_from_capture_returns_result() -> None:
    _, node, instance, _, service = make_context()

    resources = (
        service.system_service
        .get_system_resources()
    )

    interface_infos = (
        service.system_service
        .get_network_interface_infos()
    )

    result = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources,
        interface_infos=interface_infos,
    )

    assert isinstance(
        result,
        TelemetryRefreshResult,
    )

    assert result.captured_at == CAPTURED_AT
    assert result.health_diagnostic.captured_at == CAPTURED_AT


def test_refresh_from_capture_requires_resources() -> None:
    _, node, instance, _, service = make_context()

    interface_infos = (
        service.system_service
        .get_network_interface_infos()
    )

    with pytest.raises(TypeError):
        service.refresh_from_capture(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            resources=object(),  # type: ignore[arg-type]
            interface_infos=interface_infos,
        )


def test_refresh_from_capture_requires_interface_infos_tuple() -> None:
    _, node, instance, _, service = make_context()

    resources = (
        service.system_service
        .get_system_resources()
    )

    with pytest.raises(TypeError):
        service.refresh_from_capture(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            resources=resources,
            interface_infos=[],  # type: ignore[arg-type]
        )


def test_refresh_from_capture_requires_network_interface_infos() -> None:
    _, node, instance, _, service = make_context()

    resources = (
        service.system_service
        .get_system_resources()
    )

    with pytest.raises(TypeError):
        service.refresh_from_capture(
            node_id=node.node_id,
            instance_id=instance.instance_id,
            resources=resources,
            interface_infos=(
                object(),  # type: ignore[arg-type]
            ),
        )


def test_refresh_once_delegates_captured_state() -> None:
    _, node, instance, _, service = make_context()

    captured = {}

    original = service.refresh_from_capture

    def recording_refresh_from_capture(
        *,
        node_id,
        instance_id,
        resources,
        interface_infos,
    ):
        captured["resources"] = resources
        captured["interface_infos"] = interface_infos

        return original(
            node_id=node_id,
            instance_id=instance_id,
            resources=resources,
            interface_infos=interface_infos,
        )

    service.refresh_from_capture = (
        recording_refresh_from_capture
    )

    result = service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert isinstance(
        captured["resources"],
        SystemResources,
    )

    assert isinstance(
        captured["interface_infos"],
        tuple,
    )

    assert all(
        isinstance(
            interface_info,
            NetworkInterfaceInfo,
        )
        for interface_info
        in captured["interface_infos"]
    )

    assert result.captured_at == CAPTURED_AT

# ---------------------------------------------------------------------------
# NodeHealth transition -> operational event integration
# ---------------------------------------------------------------------------


def make_health_event_context():
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-primary"
    )

    registry.register(node)

    metric_service = MetricService(
        registry
    )

    health_service = HealthService(
        registry
    )

    event_service = EventService(
        registry
    )

    health_transition_event_service = (
        HealthTransitionEventService(
            event_service=event_service,
        )
    )

    system_service = FixedSystemService(
        FakeSystemAdapter()
    )

    refresh_service = TelemetryRefreshService(
        system_service=system_service,
        metric_service=metric_service,
        health_service=health_service,
        health_transition_event_service=(
            health_transition_event_service
        ),
    )

    return (
        node,
        instance,
        health_service,
        event_service,
        refresh_service,
    )


def test_first_refresh_does_not_generate_health_event() -> None:
    (
        node,
        instance,
        _,
        event_service,
        refresh_service,
    ) = make_health_event_context()

    refresh_service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert events == ()


def test_repeated_same_health_does_not_generate_event() -> None:
    (
        node,
        instance,
        _,
        event_service,
        refresh_service,
    ) = make_health_event_context()

    first_resources = (
        refresh_service.system_service
        .get_system_resources()
    )

    interface_infos = (
        refresh_service.system_service
        .get_network_interface_infos()
    )

    refresh_service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=first_resources,
        interface_infos=interface_infos,
    )

    second_resources = SystemResources(
        cpu=first_resources.cpu,
        memory=first_resources.memory,
        disk=first_resources.disk,
        network=first_resources.network,
        uptime=first_resources.uptime,
        captured_at=(
            first_resources.captured_at
            + timedelta(seconds=1)
        ),
    )

    refresh_service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=second_resources,
        interface_infos=interface_infos,
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert events == ()


def test_refresh_generates_event_when_health_changes() -> None:
    (
        node,
        instance,
        health_service,
        event_service,
        refresh_service,
    ) = make_health_event_context()

    health_service.publish(
        node.node_id,
        instance.instance_id,
        NodeHealth(
            NodeHealthState.CRITICAL
        ),
    )

    refresh_service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_type == (
        "NODE_HEALTH_RECOVERED"
    )

    assert event.attributes is not None
    assert event.attributes["previous"] == (
        "CRITICAL"
    )
    assert event.attributes["current"] == (
        "HEALTHY"
    )


def test_refresh_publishes_current_health_after_transition() -> None:
    (
        node,
        instance,
        health_service,
        event_service,
        refresh_service,
    ) = make_health_event_context()

    health_service.publish(
        node.node_id,
        instance.instance_id,
        NodeHealth(
            NodeHealthState.CRITICAL
        ),
    )

    refresh_service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    current = health_service.current(
        node.node_id,
        instance.instance_id,
    )

    assert current is not None
    assert current.state is (
        NodeHealthState.HEALTHY
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 1


def test_service_accepts_network_health_stabilizer() -> None:
    from app.noc.services.network_interface_health_stabilizer import (
        NetworkInterfaceHealthStabilizer,
    )

    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    stabilizer = NetworkInterfaceHealthStabilizer(
        degradation_seconds=2.0,
        recovery_seconds=4.0,
    )

    service = TelemetryRefreshService(
        system_service=FixedSystemService(
            FakeSystemAdapter()
        ),
        metric_service=MetricService(
            registry
        ),
        health_service=HealthService(
            registry
        ),
        network_health_stabilizer=stabilizer,
    )

    assert (
        service._network_health_stabilizer
        is stabilizer
    )


def test_service_rejects_invalid_network_health_stabilizer() -> None:
    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    with pytest.raises(
        TypeError,
        match="network_health_stabilizer",
    ):
        TelemetryRefreshService(
            system_service=FixedSystemService(
                FakeSystemAdapter()
            ),
            metric_service=MetricService(
                registry
            ),
            health_service=HealthService(
                registry
            ),
            network_health_stabilizer=object(),  # type: ignore[arg-type]
        )


def test_network_health_stabilization_across_refresh_cycles() -> None:
    """Validate temporal hysteresis through the real refresh pipeline."""

    from datetime import timedelta

    from app.noc.services.network_interface_health_stabilizer import (
        NetworkInterfaceHealthStabilizer,
    )

    (
        _,
        node,
        instance,
        _,
        service,
    ) = make_context()

    service._network_health_stabilizer = (
        NetworkInterfaceHealthStabilizer(
            degradation_seconds=3.0,
            recovery_seconds=5.0,
        )
    )

    base = (
        service.system_service
        .get_system_resources()
    )

    interface_infos = (
        service.system_service
        .get_network_interface_infos()
    )

    def resources_at(
        seconds: int,
        *,
        dropped_in_delta: int,
    ) -> SystemResources:
        """Create one deterministic monotonic network capture."""

        return SystemResources(
            cpu=base.cpu,
            memory=base.memory,
            disk=base.disk,
            network=NetworkInfo(
                interface=base.network.interface,
                bytes_sent=(
                    base.network.bytes_sent
                    + seconds * 1_000
                ),
                bytes_received=(
                    base.network.bytes_received
                    + seconds * 2_000
                ),
                packets_sent=(
                    base.network.packets_sent
                    + seconds * 10
                ),
                packets_received=(
                    base.network.packets_received
                    + seconds * 20
                ),
                errors_in=base.network.errors_in,
                errors_out=base.network.errors_out,
                dropped_in=(
                    base.network.dropped_in
                    + dropped_in_delta
                ),
                dropped_out=base.network.dropped_out,
            ),
            uptime=UptimeInfo(
                uptime_seconds=(
                    base.uptime.uptime_seconds
                    + seconds
                )
            ),
            captured_at=(
                base.captured_at
                + timedelta(seconds=seconds)
            ),
        )

    # ---------------------------------------------------------
    # t=0
    #
    # Primera captura: todavía no existen tasas temporales.
    # ---------------------------------------------------------

    initial = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            0,
            dropped_in_delta=0,
        ),
        interface_infos=interface_infos,
    )

    assert (
        initial.health_diagnostic.network_interfaces[0].state
        is NodeHealthState.UNKNOWN
    )

    # ---------------------------------------------------------
    # t=5
    #
    # Primera observación HEALTHY.
    # Como venimos de UNKNOWN, inicia confirmación temporal.
    # ---------------------------------------------------------

    healthy_candidate = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            5,
            dropped_in_delta=0,
        ),
        interface_infos=interface_infos,
    )

    assert (
        healthy_candidate
        .health_diagnostic
        .network_interfaces[0]
        .state
        is NodeHealthState.UNKNOWN
    )

    # ---------------------------------------------------------
    # t=9
    #
    # HEALTHY lleva 4 s estable (> 3 s).
    # ---------------------------------------------------------

    healthy = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            9,
            dropped_in_delta=0,
        ),
        interface_infos=interface_infos,
    )

    assert (
        healthy.health_diagnostic.network_health.state
        is NodeHealthState.HEALTHY
    )

    assert (
        healthy.health_diagnostic.network_interfaces[0].state
        is NodeHealthState.HEALTHY
    )

    # ---------------------------------------------------------
    # t=10
    #
    # +2 drops en 1 s => 2 drops/s.
    # Supera WARNING_RATE=1.0, pero solo durante 1 s.
    #
    # Debe conservar HEALTHY.
    # ---------------------------------------------------------

    warning_spike = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            10,
            dropped_in_delta=2,
        ),
        interface_infos=interface_infos,
    )

    held_interface = (
        warning_spike
        .health_diagnostic
        .network_interfaces[0]
    )

    assert (
        held_interface.state
        is NodeHealthState.HEALTHY
    )

    assert held_interface.drop_rate == pytest.approx(
        2.0
    )

    assert (
        "Temporally stabilized at HEALTHY"
        in held_interface.reason
    )

    assert (
        warning_spike.health_diagnostic.network_health.state
        is NodeHealthState.HEALTHY
    )

    # ---------------------------------------------------------
    # t=14
    #
    # El contador pasa de +2 a +10:
    #
    #   8 drops / 4 s = 2 drops/s
    #
    # WARNING lleva 4 s, por lo que debe confirmarse.
    # ---------------------------------------------------------

    warning_confirmed = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            14,
            dropped_in_delta=10,
        ),
        interface_infos=interface_infos,
    )

    assert (
        warning_confirmed
        .health_diagnostic
        .network_interfaces[0]
        .state
        is NodeHealthState.WARNING
    )

    assert (
        warning_confirmed
        .health_diagnostic
        .network_health
        .state
        is NodeHealthState.WARNING
    )

    assert (
        warning_confirmed
        .health_diagnostic
        .health
        .state
        is NodeHealthState.WARNING
    )

    # ---------------------------------------------------------
    # t=15
    #
    # No aparecen nuevos drops.
    # La observación vuelve a HEALTHY,
    # pero recuperación requiere 5 s.
    # ---------------------------------------------------------

    recovery_candidate = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            15,
            dropped_in_delta=10,
        ),
        interface_infos=interface_infos,
    )

    recovery_interface = (
        recovery_candidate
        .health_diagnostic
        .network_interfaces[0]
    )

    assert (
        recovery_interface.state
        is NodeHealthState.WARNING
    )

    assert recovery_interface.drop_rate == pytest.approx(
        0.0
    )

    assert (
        "Temporally stabilized at WARNING"
        in recovery_interface.reason
    )

    # ---------------------------------------------------------
    # t=20
    #
    # HEALTHY lleva exactamente 5 s:
    # recuperación confirmada.
    # ---------------------------------------------------------

    recovered = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            20,
            dropped_in_delta=10,
        ),
        interface_infos=interface_infos,
    )

    assert (
        recovered.health_diagnostic.network_health.state
        is NodeHealthState.HEALTHY
    )

    assert (
        recovered.health_diagnostic.health.state
        is NodeHealthState.HEALTHY
    )

    # ---------------------------------------------------------
    # t=21
    #
    # Pérdida física de carrier:
    # CRITICAL nunca espera confirmación temporal.
    # ---------------------------------------------------------

    original_info = interface_infos[0]

    critical_infos = (
        NetworkInterfaceInfo(
            interface=original_info.interface,
            interface_type=original_info.interface_type,
            is_up=True,
            carrier=False,
            mtu=original_info.mtu,
            link_speed_mbps=(
                original_info.link_speed_mbps
            ),
        ),
    )

    critical = service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=resources_at(
            21,
            dropped_in_delta=10,
        ),
        interface_infos=critical_infos,
    )

    assert (
        critical.health_diagnostic.network_interfaces[0].state
        is NodeHealthState.CRITICAL
    )

    assert (
        critical.health_diagnostic.network_health.state
        is NodeHealthState.CRITICAL
    )

    assert (
        critical.health_diagnostic.health.state
        is NodeHealthState.CRITICAL
    )


# ---------------------------------------------------------------------------
# NodeHealth transition -> operational alarm integration
# ---------------------------------------------------------------------------


def make_health_alarm_context():
    """Build a real Event + Alarm transition integration context."""

    from app.noc.services.alarm_service import AlarmService
    from app.noc.services.health_transition_alarm_service import (
        HealthTransitionAlarmService,
    )

    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-alarm-core",
            name="streaming-alarm",
            display_name="Streaming Alarm Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-alarm-primary"
    )

    registry.register(node)

    metric_service = MetricService(
        registry
    )

    health_service = HealthService(
        registry
    )

    event_service = EventService(
        registry
    )

    alarm_service = AlarmService(
        registry
    )

    health_transition_event_service = (
        HealthTransitionEventService(
            event_service=event_service,
        )
    )

    health_transition_alarm_service = (
        HealthTransitionAlarmService(
            alarm_service=alarm_service,
        )
    )

    system_service = FixedSystemService(
        FakeSystemAdapter()
    )

    refresh_service = TelemetryRefreshService(
        system_service=system_service,
        metric_service=metric_service,
        health_service=health_service,
        health_transition_event_service=(
            health_transition_event_service
        ),
        health_transition_alarm_service=(
            health_transition_alarm_service
        ),
    )

    return (
        node,
        instance,
        health_service,
        event_service,
        alarm_service,
        refresh_service,
    )


def make_critical_health_alarm_context():
    """Build runtime context whose required ingest NIC is down."""

    from app.noc.domain.network_interface_policy import (
        NetworkInterfacePolicy,
        NetworkInterfaceRole,
    )
    from app.noc.services.alarm_service import AlarmService
    from app.noc.services.health_transition_alarm_service import (
        HealthTransitionAlarmService,
    )

    repository = InMemoryNodeRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NodeId.create(
            id="streaming-critical-core",
            name="streaming-critical",
            display_name="Streaming Critical Core",
        ),
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id="streaming-critical-primary"
    )

    registry.register(node)

    metric_service = MetricService(
        registry
    )

    health_service = HealthService(
        registry
    )

    event_service = EventService(
        registry
    )

    alarm_service = AlarmService(
        registry
    )

    health_transition_event_service = (
        HealthTransitionEventService(
            event_service=event_service,
        )
    )

    health_transition_alarm_service = (
        HealthTransitionAlarmService(
            alarm_service=alarm_service,
        )
    )

    system_service = NetworkPolicySystemService(
        NetworkPolicySystemAdapter(
            interface="enp9s0",
            is_up=False,
            carrier=False,
        )
    )

    policy = NetworkInterfacePolicy(
        interface="enp9s0",
        role=NetworkInterfaceRole.INGEST,
        expected_up=True,
        critical=True,
    )

    refresh_service = TelemetryRefreshService(
        system_service=system_service,
        metric_service=metric_service,
        health_service=health_service,
        health_transition_event_service=(
            health_transition_event_service
        ),
        health_transition_alarm_service=(
            health_transition_alarm_service
        ),
        network_policies=(policy,),
    )

    return (
        node,
        instance,
        health_service,
        event_service,
        alarm_service,
        refresh_service,
    )


def test_first_refresh_does_not_generate_operational_alarm() -> None:
    (
        node,
        instance,
        _,
        _,
        alarm_service,
        refresh_service,
    ) = make_health_alarm_context()

    refresh_service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    assert alarm_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_repeated_same_health_does_not_generate_operational_alarm() -> None:
    (
        node,
        instance,
        _,
        _,
        alarm_service,
        refresh_service,
    ) = make_health_alarm_context()

    first_resources = (
        refresh_service.system_service
        .get_system_resources()
    )

    interface_infos = (
        refresh_service.system_service
        .get_network_interface_infos()
    )

    refresh_service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=first_resources,
        interface_infos=interface_infos,
    )

    second_resources = SystemResources(
        cpu=first_resources.cpu,
        memory=first_resources.memory,
        disk=first_resources.disk,
        network=first_resources.network,
        uptime=first_resources.uptime,
        captured_at=(
            first_resources.captured_at
            + timedelta(seconds=1)
        ),
    )

    refresh_service.refresh_from_capture(
        node_id=node.node_id,
        instance_id=instance.instance_id,
        resources=second_resources,
        interface_infos=interface_infos,
    )

    assert alarm_service.list_all(
        node.node_id,
        instance.instance_id,
    ) == ()


def test_health_degradation_generates_event_and_alarm() -> None:
    from app.noc.domain.node_alarm import (
        AlarmSeverity,
        AlarmState,
    )

    (
        node,
        instance,
        health_service,
        event_service,
        alarm_service,
        refresh_service,
    ) = make_critical_health_alarm_context()

    # Establish a previous healthy operational state.
    health_service.publish(
        node.node_id,
        instance.instance_id,
        NodeHealth(
            NodeHealthState.HEALTHY
        ),
    )

    refresh_service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    alarms = alarm_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 1
    assert len(alarms) == 1

    event = events[0]
    alarm = alarms[0]

    assert event.event_type == (
        "NODE_HEALTH_DEGRADED"
    )
    assert event.attributes is not None
    assert event.attributes["previous"] == (
        "HEALTHY"
    )
    assert event.attributes["current"] == (
        "CRITICAL"
    )

    assert alarm.alarm_type == (
        "NODE_HEALTH_DEGRADED"
    )
    assert alarm.severity is (
        AlarmSeverity.CRITICAL
    )
    assert alarm.state is AlarmState.ACTIVE

    assert alarm.attributes is not None
    assert alarm.attributes["previous"] == (
        "HEALTHY"
    )
    assert alarm.attributes["current"] == (
        "CRITICAL"
    )


def test_health_recovery_resolves_existing_operational_alarm() -> None:
    from app.noc.domain.node_alarm import AlarmState
    from app.noc.services.health_transition_alarm_factory import (
        HealthTransitionAlarmFactory,
    )
    from app.noc.services.health_transition_detector import (
        HealthTransitionDetector,
    )

    (
        node,
        instance,
        health_service,
        event_service,
        alarm_service,
        refresh_service,
    ) = make_health_alarm_context()

    detector = HealthTransitionDetector()
    factory = HealthTransitionAlarmFactory()

    degradation = detector.detect(
        previous=NodeHealth(
            NodeHealthState.HEALTHY
        ),
        current=NodeHealth(
            NodeHealthState.CRITICAL
        ),
    )

    assert degradation is not None

    active_alarm = factory.create(
        transition=degradation,
        source=instance.instance_id,
        timestamp=CAPTURED_AT,
    )

    assert active_alarm is not None

    alarm_service.raise_alarm(
        node.node_id,
        instance.instance_id,
        active_alarm,
    )

    health_service.publish(
        node.node_id,
        instance.instance_id,
        NodeHealth(
            NodeHealthState.CRITICAL
        ),
    )

    refresh_service.refresh_once(
        node_id=node.node_id,
        instance_id=instance.instance_id,
    )

    events = event_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    alarms = alarm_service.list_all(
        node.node_id,
        instance.instance_id,
    )

    assert len(events) == 1
    assert len(alarms) == 1

    event = events[0]
    resolved = alarms[0]

    assert event.event_type == (
        "NODE_HEALTH_RECOVERED"
    )
    assert event.attributes is not None
    assert event.attributes["previous"] == (
        "CRITICAL"
    )
    assert event.attributes["current"] == (
        "HEALTHY"
    )

    assert resolved.alarm_id == (
        active_alarm.alarm_id
    )
    assert resolved.state is AlarmState.RESOLVED
    assert resolved.resolved_at == CAPTURED_AT

    assert alarm_service.active(
        node.node_id,
        instance.instance_id,
    ) == ()
