"""Pruebas de los modelos de presentación del dashboard."""

from datetime import datetime, timezone

import pytest

from app.dashboard.models.dashboard_models import (
    DashboardData,
    PathRowData,
    ServerPanelData,
    StreamingPanelData,
)


def test_server_panel_data_stores_expected_values() -> None:
    snapshot_at = datetime(2026, 7, 20, 18, 30, tzinfo=timezone.utc)

    data = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=snapshot_at,
        quality="AVAILABLE",
    )

    assert data.hostname == "server-01"
    assert data.mediamtx_online is True
    assert data.api_online is True
    assert data.snapshot_at == snapshot_at
    assert data.quality == "AVAILABLE"


def test_streaming_panel_data_stores_expected_values() -> None:
    data = StreamingPanelData(
        active_paths=2,
        readers=5,
        inbound_bitrate_bps=6_000_000,
        outbound_bitrate_bps=18_000_000,
        quality="AVAILABLE",
    )

    assert data.active_paths == 2
    assert data.readers == 5
    assert data.inbound_bitrate_bps == 6_000_000
    assert data.outbound_bitrate_bps == 18_000_000
    assert data.quality == "AVAILABLE"


def test_path_row_data_stores_expected_values() -> None:
    data = PathRowData(
        name="canal-principal",
        status="ACTIVE",
        readers=3,
        inbound_bitrate_bps=4_000_000,
        outbound_bitrate_bps=12_000_000,
        quality="AVAILABLE",
        source="udpSource",
    )

    assert data.name == "canal-principal"
    assert data.status == "ACTIVE"
    assert data.readers == 3
    assert data.source == "udpSource"


def test_dashboard_data_groups_all_sections() -> None:
    server = ServerPanelData(
        hostname="server-01",
        mediamtx_online=True,
        api_online=True,
        snapshot_at=None,
        quality="NOT_AVAILABLE",
    )

    streaming = StreamingPanelData(
        active_paths=0,
        readers=0,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality="NOT_AVAILABLE",
    )

    dashboard = DashboardData(
        server=server,
        streaming=streaming,
        paths=(),
    )

    assert dashboard.server is server
    assert dashboard.streaming is streaming
    assert dashboard.paths == ()


def test_streaming_panel_rejects_negative_active_paths() -> None:
    with pytest.raises(ValueError):
        StreamingPanelData(
            active_paths=-1,
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
        )


def test_streaming_panel_rejects_negative_readers() -> None:
    with pytest.raises(ValueError):
        StreamingPanelData(
            active_paths=0,
            readers=-1,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
        )


def test_path_row_rejects_negative_readers() -> None:
    with pytest.raises(ValueError):
        PathRowData(
            name="canal-principal",
            status="ACTIVE",
            readers=-1,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
            source="udpSource",
        )


def test_path_row_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        PathRowData(
            name="   ",
            status="ACTIVE",
            readers=0,
            inbound_bitrate_bps=None,
            outbound_bitrate_bps=None,
            quality="NOT_AVAILABLE",
            source="N/D",
        )
