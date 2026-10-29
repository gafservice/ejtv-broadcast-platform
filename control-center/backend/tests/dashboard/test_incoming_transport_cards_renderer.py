"""RED contract for INCOMING V2 TRANSPORT six-card renderer."""

from dataclasses import replace

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.domain.streaming.health import HealthStatus


def make_data():
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=2.21,
                health_status=HealthStatus.DEGRADED,
                transport_health_status=HealthStatus.HEALTHY,
                protocol="UDP",
                remote_address="10.0.18.51:3000",
                health_reason="Media degraded",
            ),
            IncomingRowData(
                path_name="impact",
                source="SRT",
                status="ACTIVE",
                bitrate_receive_mbps=5.87,
                health_status=HealthStatus.HEALTHY,
                transport_health_status=HealthStatus.CRITICAL,
                protocol="SRT",
                remote_address="192.0.2.30:8050",
            ),
        )
    )


def render_transport(data, selected_path_name):
    from app.dashboard.renderers.incoming_transport_cards_renderer import (
        IncomingTransportCardsRenderer,
    )

    panel = IncomingTransportCardsRenderer().render(
        data,
        selected_path_name=selected_path_name,
    )

    console = Console(
        width=122,
        height=40,
        force_terminal=False,
        color_system=None,
    )

    with console.capture() as capture:
        console.print(panel)

    return panel, capture.get()


def test_transport_has_six_cards():
    panel, screen = render_transport(make_data(), "ejtv")

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Table)
    assert "TRANSPORT DETAIL" in panel.title

    for title in (
        "CONNECTION",
        "TRAFFIC",
        "PACKET QUALITY",
        "LATENCY",
        "STABILITY",
        "TRANSPORT HEALTH",
    ):
        assert title in screen


def test_transport_uses_selected_path_only():
    _, screen = render_transport(make_data(), "ejtv")

    assert "ejtv" in screen
    assert "UDP" in screen
    assert "10.0.18.51:3000" in screen
    assert "2.21 Mbps" in screen

    assert "192.0.2.30:8050" not in screen
    assert "5.87 Mbps" not in screen


def test_transport_health_is_not_aggregate_signal_health():
    _, screen = render_transport(make_data(), "ejtv")

    assert "TRANSPORT HEALTH" in screen
    assert "HEALTHY" in screen

    assert "DEGRADED" not in screen
    assert "Media degraded" not in screen


def test_transport_unavailable_metrics_are_explicit():
    _, screen = render_transport(make_data(), "ejtv")

    for label in (
        "Packet Loss",
        "Retransmissions",
        "Jitter",
        "RTT",
        "SRT Latency",
        "Observed Recoveries",
        "Availability",
    ):
        assert label in screen

    assert screen.count("N/A") >= 7


def test_transport_uses_canonical_transport_health():
    _, screen = render_transport(make_data(), "impact")

    assert "CRITICAL" in screen
    assert "192.0.2.30:8050" in screen

    assert "10.0.18.51:3000" not in screen


def test_transport_does_not_invent_missing_values():
    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="unknown",
                source="N/A",
                status="ACTIVE",
                bitrate_receive_mbps=None,
                health_status=HealthStatus.HEALTHY,
                transport_health_status=None,
                protocol=None,
                remote_address=None,
            ),
        )
    )

    _, screen = render_transport(data, "unknown")

    assert "TRANSPORT HEALTH" in screen
    assert "N/A" in screen
    assert "HEALTHY" not in screen


@pytest.mark.parametrize(
    "selected_path_name",
    (None, "nonexistent"),
)
def test_transport_requires_valid_selection(selected_path_name):
    panel, screen = render_transport(
        make_data(),
        selected_path_name,
    )

    assert isinstance(panel, Panel)
    assert "No incoming signal selected." in screen
    assert "10.0.18.51:3000" not in screen
    assert "192.0.2.30:8050" not in screen


def test_stability_renders_observed_counter_values():
    original_data = make_data()

    rows = tuple(
        replace(
            row,
            transport_observed_interruptions=2,
            transport_observed_recoveries=1,
        )
        if row.path_name == "ejtv"
        else row
        for row in original_data.rows
    )

    data = replace(original_data, rows=rows)

    _, screen = render_transport(data, "ejtv")

    assert "STABILITY" in screen
    assert "Observed Recoveries" in screen
    assert "Interruptions" in screen

    import re

    assert re.search(
        r"Observed Recoveries\s+1(?:\s|$)",
        screen,
    )

    assert re.search(
        r"Interruptions\s+2(?:\s|$)",
        screen,
    )


def test_stability_renders_unknown_counters_as_na():
    data = make_data()

    _, screen = render_transport(data, "ejtv")

    import re

    assert re.search(
        r"Observed Recoveries\s+N/A",
        screen,
    )

    assert re.search(
        r"Interruptions\s+N/A",
        screen,
    )
