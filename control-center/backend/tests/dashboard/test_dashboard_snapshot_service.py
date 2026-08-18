"""Tests para DashboardSnapshotService."""

from datetime import UTC, datetime

from app.dashboard.models import (
    NetworkInterfaceRowData,
    NetworkInterfacesPanelData,
)
from app.dashboard.services.dashboard_snapshot_service import (
    DashboardSnapshotInput,
    DashboardSnapshotService,
)
from app.domain.streaming import (
    MeasurementQuality,
    MediaMTXSnapshot,
    StreamingMeasurement,
)


def test_snapshot_service_transports_network_interfaces() -> None:
    captured_at = datetime(
        2026,
        8,
        18,
        19,
        45,
        tzinfo=UTC,
    )

    snapshot = MediaMTXSnapshot(
        captured_at=captured_at,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=captured_at,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    network_interfaces = NetworkInterfacesPanelData(
        interfaces=(
            NetworkInterfaceRowData(
                interface="ens2f0",
                interface_type="ETHERNET",
                is_up=True,
                carrier=True,
                link_speed_mbps=100,
                mtu=1500,
                mac_address="00:e0:ed:2c:6d:c0",
                ipv4_addresses=("172.16.30.35",),
                ipv6_addresses=(),
                rx_bps=60_000.0,
                tx_bps=4_900_000.0,
                errors_in=0,
                errors_out=0,
                dropped_in=0,
                dropped_out=0,
            ),
        ),
        captured_at=captured_at,
    )

    result = DashboardSnapshotService().build_snapshot(
        DashboardSnapshotInput(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot=snapshot,
            measurement=measurement,
            network_interfaces=network_interfaces,
        )
    )

    assert result.network_interfaces is network_interfaces
    assert (
        result.network_interfaces.interfaces[0].interface
        == "ens2f0"
    )
