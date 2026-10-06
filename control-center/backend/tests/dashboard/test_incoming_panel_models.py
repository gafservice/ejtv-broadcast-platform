"""Contract tests for the INCOMING dashboard presentation models."""

import pytest

from app.domain.streaming.health import HealthStatus
from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)


def test_incoming_row_carries_path_first_presentation_data() -> None:
    row = IncomingRowData(
        path_name="service-a",
        source="external publisher",
        status="ready",
        bitrate_receive_mbps=5.75,
        health_status=HealthStatus.HEALTHY,
        protocol="SRT",
        remote_address="192.0.2.10:9000",
    )

    assert row.path_name == "service-a"
    assert row.source == "external publisher"
    assert row.status == "ready"
    assert row.bitrate_receive_mbps == 5.75
    assert row.health_status is HealthStatus.HEALTHY
    assert row.protocol == "SRT"
    assert row.remote_address == "192.0.2.10:9000"


def test_incoming_row_allows_missing_optional_publisher_evidence() -> None:
    row = IncomingRowData(
        path_name="service-b",
        source="observed path",
        status="ready",
        bitrate_receive_mbps=None,
        health_status=None,
    )

    assert row.protocol is None
    assert row.remote_address is None


def test_incoming_panel_defaults_to_empty_rows() -> None:
    panel = IncomingPanelData()

    assert panel.rows == ()


def test_incoming_panel_preserves_immutable_rows() -> None:
    row = IncomingRowData(
        path_name="service-a",
        source="external publisher",
        status="ready",
        bitrate_receive_mbps=5.75,
        health_status=HealthStatus.HEALTHY,
    )
    panel = IncomingPanelData(rows=(row,))

    assert panel.rows == (row,)

    with pytest.raises(AttributeError):
        panel.rows = ()


def test_incoming_row_is_immutable() -> None:
    row = IncomingRowData(
        path_name="service-a",
        source="observed path",
        status="ready",
        bitrate_receive_mbps=None,
        health_status=None,
    )

    with pytest.raises(AttributeError):
        row.status = "changed"


def test_dashboard_data_accepts_optional_incoming_panel() -> None:
    """DashboardData debe transportar INCOMING sin hacerlo obligatorio."""

    from datetime import datetime, timezone

    from app.dashboard.models import (
        DashboardData,
        PathRowData,
        ServerPanelData,
        StreamingPanelData,
    )

    incoming = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="service-alpha",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=5.0,
                health_status=None,
            ),
        ),
    )

    data = DashboardData(
        server=ServerPanelData(
            hostname="server-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=datetime(
                2026, 10, 6, 1, 30, tzinfo=timezone.utc
            ),
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=1,
            readers=0,
            inbound_bitrate_bps=5_000_000,
            outbound_bitrate_bps=0,
            quality="AVAILABLE",
        ),
        paths=(
            PathRowData(
                name="service-alpha",
                source="SRT",
                readers=0,
                inbound_bitrate_bps=5_000_000,
                outbound_bitrate_bps=0,
                status="ACTIVE",
                quality="AVAILABLE",
            ),
        ),
        incoming=incoming,
    )

    assert data.incoming is incoming


def test_dashboard_data_preserves_legacy_construction_without_incoming() -> None:
    """INCOMING debe ser opcional para callers históricos."""

    from datetime import datetime, timezone

    from app.dashboard.models import (
        DashboardData,
        ServerPanelData,
        StreamingPanelData,
    )

    data = DashboardData(
        server=ServerPanelData(
            hostname="server-01",
            mediamtx_online=True,
            api_online=True,
            snapshot_at=datetime(
                2026, 10, 6, 1, 35, tzinfo=timezone.utc
            ),
            quality="AVAILABLE",
        ),
        streaming=StreamingPanelData(
            active_paths=0,
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
        ),
        paths=(),
    )

    assert data.incoming is None
