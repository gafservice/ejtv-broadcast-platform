"""Contract for four INCOMING V2 SIGNAL information cards."""

from datetime import datetime, timedelta, timezone

import pytest
from rich.console import Console

from app.domain.streaming.health import HealthStatus
from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)


REFERENCE = datetime(
    2026, 10, 15, 20, 0, 0,
    tzinfo=timezone.utc,
)


def render_cards(data, selected_path_name):
    from app.dashboard.renderers.incoming_signal_cards_renderer import (
        IncomingSignalCardsRenderer,
    )

    panel = IncomingSignalCardsRenderer().render(
        data,
        selected_path_name=selected_path_name,
    )

    console = Console(
        width=122,
        height=30,
        force_terminal=False,
        color_system=None,
    )

    with console.capture() as capture:
        console.print(panel)

    return capture.get()


def make_data():
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=2.21,
                health_status=HealthStatus.HEALTHY,
                protocol="UDP",
                remote_address="10.0.18.51:3000",
                health_reason=None,
                health_since=REFERENCE - timedelta(
                    hours=1,
                    minutes=2,
                    seconds=7,
                ),
                alarm_count=0,
                alarm_severity=None,
            ),
            IncomingRowData(
                path_name="impact",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=5.87,
                health_status=HealthStatus.CRITICAL,
                protocol="SRT",
                remote_address="192.0.2.30:8050",
                health_reason="Packet loss detected",
                alarm_count=2,
                alarm_severity="MAJOR",
            ),
        ),
        reference_at=REFERENCE,
    )


def test_cards_have_four_sections():
    screen = render_cards(make_data(), "ejtv")

    for title in (
        "IDENTIFICACIÓN",
        "RECEPCIÓN",
        "HEALTH",
        "ALARMAS",
    ):
        assert title in screen


def test_cards_use_selected_signal_only():
    screen = render_cards(make_data(), "ejtv")

    assert "ejtv" in screen
    assert "MPEG-TS" in screen
    assert "UDP" in screen
    assert "10.0.18.51:3000" in screen
    assert "2.21 Mbps" in screen
    assert "HEALTHY" in screen

    assert "192.0.2.30:8050" not in screen
    assert "Packet loss detected" not in screen
    assert "5.87 Mbps" not in screen


def test_cards_preserve_canonical_health_duration():
    screen = render_cards(make_data(), "ejtv")

    assert "01:02:07" in screen


def test_cards_do_not_invent_reception_timestamps():
    screen = render_cards(make_data(), "ejtv")

    assert "RECEPCIÓN" in screen
    assert "Since" in screen
    assert "Duration" in screen
    assert screen.count("N/A") >= 2


def test_cards_preserve_alarm_evidence():
    screen = render_cards(make_data(), "impact")

    assert "CRITICAL" in screen
    assert "Packet loss detected" in screen
    assert "2" in screen
    assert "MAJOR" in screen


@pytest.mark.parametrize(
    "selected_path_name",
    (None, "unknown"),
)
def test_cards_do_not_substitute_missing_selection(
    selected_path_name,
):
    screen = render_cards(
        make_data(),
        selected_path_name,
    )

    assert "No incoming signal selected." in screen
    assert "10.0.18.51:3000" not in screen
    assert "192.0.2.30:8050" not in screen
