"""Presentation contract for INCOMING 60-second bitrate statistics."""

from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace

import pytest
from rich.console import Console

from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)


def render_transport(
    *,
    receive: float | None,
    average: float | None,
    minimum: float | None,
    maximum: float | None,
) -> str:
    """Render one selected path without depending on capture hardware."""

    selected = SimpleNamespace(
        path_name="impact",
        protocol="srt",
        remote_address="192.0.2.10",
        status="ready",
        transport_source_type="publisher",
        bitrate_receive_mbps=receive,
        bitrate_average_mbps=average,
        bitrate_minimum_mbps=minimum,
        bitrate_maximum_mbps=maximum,
        transport_received_bytes=1000,
        transport_health_status=None,
        transport_available=True,
        transport_observed_at=None,
    )

    data = SimpleNamespace(
        rows=(selected,),
        reference_at=datetime(
            2026, 10, 19, 12, 0, tzinfo=timezone.utc
        ),
    )

    panel = IncomingTransportCardsRenderer().render(
        data,
        selected_path_name="impact",
        compact=False,
    )

    output = StringIO()

    console = Console(
        file=output,
        width=120,
        force_terminal=False,
        color_system=None,
    )

    console.print(panel)

    return output.getvalue()


def test_transport_traffic_displays_independent_statistics():
    output = render_transport(
        receive=6.25,
        average=5.80,
        minimum=4.70,
        maximum=7.10,
    )

    assert "Receive" in output
    assert "6.25 Mbps" in output

    assert "Average" in output
    assert "5.80 Mbps" in output

    assert "Minimum" in output
    assert "4.70 Mbps" in output

    assert "Maximum" in output
    assert "7.10 Mbps" in output


def test_transport_traffic_preserves_valid_zero():
    output = render_transport(
        receive=0.0,
        average=0.0,
        minimum=0.0,
        maximum=0.0,
    )

    assert output.count("0.00 Mbps") >= 4


def test_transport_traffic_preserves_unavailable_statistics():
    output = render_transport(
        receive=6.25,
        average=None,
        minimum=None,
        maximum=None,
    )

    assert "6.25 Mbps" in output

    for label in ("Average", "Minimum", "Maximum"):
        assert label in output

    assert output.count("N/A") >= 3
