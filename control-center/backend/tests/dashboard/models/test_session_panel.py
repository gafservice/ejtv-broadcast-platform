"""Pruebas del modelo de presentación SessionPanelData."""

from dataclasses import FrozenInstanceError

import pytest

from app.dashboard.models import SessionPanelData


def build_panel_data() -> SessionPanelData:
    """Construye datos válidos para el panel ACTIVE CLIENTS."""

    return SessionPanelData(
        total_sessions=12,
        readers=10,
        publishers=2,
        degraded_sessions=3,
        critical_sessions=1,
        inbound_bitrate_bps=8_500_000.0,
        outbound_bitrate_bps=42_000_000.0,
        quality="POOR",
    )


def test_session_panel_data_can_be_created() -> None:
    data = build_panel_data()

    assert data.total_sessions == 12
    assert data.readers == 10
    assert data.publishers == 2
    assert data.degraded_sessions == 3
    assert data.critical_sessions == 1
    assert data.inbound_bitrate_bps == 8_500_000.0
    assert data.outbound_bitrate_bps == 42_000_000.0
    assert data.quality == "POOR"


def test_session_panel_data_accepts_unavailable_bitrates() -> None:
    data = SessionPanelData(
        total_sessions=0,
        readers=0,
        publishers=0,
        degraded_sessions=0,
        critical_sessions=0,
        inbound_bitrate_bps=None,
        outbound_bitrate_bps=None,
        quality="UNKNOWN",
    )

    assert data.inbound_bitrate_bps is None
    assert data.outbound_bitrate_bps is None
    assert data.quality == "UNKNOWN"


def test_session_panel_data_instances_with_same_values_are_equal() -> None:
    first = build_panel_data()
    second = build_panel_data()

    assert first == second


def test_session_panel_data_is_immutable() -> None:
    data = build_panel_data()

    with pytest.raises(FrozenInstanceError):
        data.total_sessions = 99
