from datetime import UTC, datetime
from unittest.mock import Mock

from rich.console import Console

from app.dashboard.models.capacity_panel import (
    CapacityPanelData,
    CapacityResourceRowData,
)
from app.dashboard.models.dashboard_models import (
    DashboardData,
    ServerPanelData,
    StreamingPanelData,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.services.dashboard_service import DashboardService
from app.noc.domain.node_capacity import CapacityResource, NodeCapacity


SNAPSHOT_AT = datetime(
    2026,
    10,
    2,
    16,
    30,
    tzinfo=UTC,
)


def _dashboard_data(
    *,
    capacity: CapacityPanelData | None = None,
) -> DashboardData:
    return DashboardData(
        server=ServerPanelData(
            hostname="ejtv-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=SNAPSHOT_AT,
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=0,
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="AVAILABLE",
        ),
        paths=(),
        capacity=capacity,
    )


def _capacity() -> NodeCapacity:
    return NodeCapacity(
        resources=(
            CapacityResource(
                resource="System Memory",
                maximum=8_000_000_000,
                allocated=3_000_000_000,
                reserved=0,
                available=5_000_000_000,
                unit="bytes",
            ),
            CapacityResource(
                resource="Streaming Channels",
                maximum=16,
                allocated=10,
                reserved=2,
                available=4,
                unit="channels",
            ),
        ),
    )


def test_dashboard_service_projects_capacity_from_noc_snapshot() -> None:
    service = DashboardService()

    noc_snapshot = Mock()
    noc_snapshot.capacity = _capacity()
    noc_snapshot.snapshot_timestamp = SNAPSHOT_AT

    panel = service.build_capacity_panel(
        noc_snapshot
    )

    assert isinstance(panel, CapacityPanelData)
    assert panel.captured_at == SNAPSHOT_AT
    assert panel.resources[0].resource == "System Memory"
    assert panel.resources[1].resource == "Streaming Channels"


def test_dashboard_service_omits_capacity_without_canonical_capacity() -> None:
    service = DashboardService()

    noc_snapshot = Mock()
    noc_snapshot.capacity = None
    noc_snapshot.snapshot_timestamp = SNAPSHOT_AT

    panel = service.build_capacity_panel(
        noc_snapshot
    )

    assert panel is None


def test_dashboard_renderer_renders_capacity_when_present() -> None:
    capacity = CapacityPanelData.from_capacity(
        _capacity(),
        captured_at=SNAPSHOT_AT,
    )

    data = _dashboard_data(
        capacity=capacity,
    )

    renderer = DashboardRenderer()
    layout = renderer.render(data)

    console = Console(
        record=True,
        width=180,
        height=80,
        color_system=None,
    )
    console.print(layout)

    output = console.export_text()

    assert "CAPACITY" in output
    assert "System Memory" in output
    assert "Streaming Channels" in output
    assert "37.5%" in output
    assert "62.5%" in output


def test_dashboard_renderer_omits_capacity_when_absent() -> None:
    data = _dashboard_data()

    assert data.capacity is None

    renderer = DashboardRenderer()
    layout = renderer.render(data)

    child_names = [
        child.name
        for child in layout.children
    ]

    assert "capacity" not in child_names


def test_build_dashboard_projects_capacity_automatically() -> None:
    service = DashboardService()

    noc_snapshot = Mock()
    noc_snapshot.capacity = _capacity()
    noc_snapshot.snapshot_timestamp = SNAPSHOT_AT

    data = _dashboard_data()

    result = service.build_dashboard(
        server=data.server,
        streaming=data.streaming,
        paths=data.paths,
        noc_snapshot=noc_snapshot,
    )

    assert result.noc_snapshot is noc_snapshot
    assert result.capacity is not None
    assert result.capacity.captured_at == SNAPSHOT_AT
    assert result.capacity.resources == (
        CapacityResourceRowData(
            resource="System Memory",
            maximum=8_000_000_000,
            allocated=3_000_000_000,
            reserved=0,
            available=5_000_000_000,
            unit="bytes",
            utilization_percent=37.5,
        ),
        CapacityResourceRowData(
            resource="Streaming Channels",
            maximum=16,
            allocated=10,
            reserved=2,
            available=4,
            unit="channels",
            utilization_percent=62.5,
        ),
    )


def test_build_dashboard_from_measurement_projects_capacity_automatically() -> None:
    from app.domain.streaming import (
        MeasurementQuality,
        MediaMTXSnapshot,
        StreamingMeasurement,
    )

    service = DashboardService()

    media_snapshot = MediaMTXSnapshot(
        captured_at=SNAPSHOT_AT,
        paths=(),
        reported_item_count=0,
        reported_page_count=0,
    )

    measurement = StreamingMeasurement(
        captured_at=SNAPSHOT_AT,
        previous_captured_at=None,
        interval_seconds=None,
        paths=(),
        total_inbound_bitrate_bps=None,
        total_outbound_bitrate_bps=None,
        quality=MeasurementQuality.NOT_AVAILABLE,
    )

    noc_snapshot = Mock()
    noc_snapshot.capacity = _capacity()
    noc_snapshot.snapshot_timestamp = SNAPSHOT_AT

    result = service.build_dashboard_from_measurement(
        hostname="ejtv-01",
        mediamtx_online=True,
        api_online=True,
        snapshot=media_snapshot,
        measurement=measurement,
        noc_snapshot=noc_snapshot,
    )

    assert result.noc_snapshot is noc_snapshot
    assert result.capacity is not None
    assert result.capacity.captured_at == SNAPSHOT_AT
    assert tuple(
        resource.resource
        for resource in result.capacity.resources
    ) == (
        "System Memory",
        "Streaming Channels",
    )
