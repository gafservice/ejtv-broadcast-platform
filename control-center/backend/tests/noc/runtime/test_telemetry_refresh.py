"""Tests for TelemetryRefreshService."""

from datetime import datetime, timezone

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
