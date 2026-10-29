"""OBS-003B.1 — SRT ingress RTT dashboard rendering contract."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from rich.console import Console

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.sessions import SessionRole
from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportMetricObservation,
    TransportQualityObservation,
)


OBSERVED_AT = datetime(2026, 10, 29, 12, 0, tzinfo=timezone.utc)


def make_panel():
    row = IncomingRowData(
        path_name="impact",
        source="SRT",
        status="READY",
        bitrate_receive_mbps=6.0,
        health_status=None,
        protocol="SRT",
        transport_source_type="srtConn",
        transport_source_id="srt-publisher-001",
    )

    return IncomingPanelData(
        rows=(row,),
        reference_at=OBSERVED_AT,
    )


def make_observation(
    *,
    role=SessionRole.PUBLISHER,
    connection_id="srt-publisher-001",
    source_id="srt-publisher-001",
    availability=EvidenceAvailability.AVAILABLE,
    value=8.25,
):
    metric = TransportMetricObservation(
        metric_name="srt.connection.rtt",
        value=value,
        unit="ms",
        availability=availability,
        source="mediamtx.metrics",
        connection_id=connection_id,
        connection_role=role,
        measurement_scope="CONNECTION",
    )

    return TransportQualityObservation(
        service_id="impact",
        path_name="impact",
        source_type="srtConn",
        source_id=source_id,
        observed_at=OBSERVED_AT,
        availability=EvidenceAvailability.AVAILABLE,
        metrics=(metric,),
    )


def render_text(observations, *, compact):
    renderer = IncomingTransportCardsRenderer()

    panel = renderer.render(
        make_panel(),
        selected_path_name="impact",
        compact=compact,
        transport_quality_observations=observations,
    )

    console = Console(
        width=140,
        force_terminal=False,
        color_system=None,
        record=True,
    )

    console.print(panel)

    return console.export_text()



def assert_rtt_row(output: str, expected: str) -> None:
    """Verify the RTT row in the rendered transport panel."""
    matches = []

    for line in output.splitlines():
        cleaned = line.replace("│", " ").strip()
        parts = cleaned.split()

        for index, part in enumerate(parts):
            if part != "RTT":
                continue

            if index + 1 >= len(parts):
                continue

            value = parts[index + 1]

            if value == "N/A":
                matches.append("N/A")
            elif (
                index + 2 < len(parts)
                and parts[index + 2] == "ms"
            ):
                matches.append(f"{value} ms")

    assert matches == [expected], (
        f"Expected RTT {expected!r}, found {matches!r}"
    )


@pytest.mark.parametrize("compact", [False, True])
def test_valid_publisher_rtt_is_visible(compact):
    observation = make_observation()

    output = render_text(
        (observation,),
        compact=compact,
    )

    assert_rtt_row(output, "8.25 ms")


@pytest.mark.parametrize("compact", [False, True])
def test_reader_rtt_is_not_attributed_to_ingress(compact):
    observation = make_observation(
        role=SessionRole.READER,
    )

    output = render_text(
        (observation,),
        compact=compact,
    )

    assert_rtt_row(output, "N/A")


@pytest.mark.parametrize("compact", [False, True])
def test_wrong_connection_identity_is_rejected(compact):
    observation = make_observation(
        connection_id="another-connection",
    )

    output = render_text(
        (observation,),
        compact=compact,
    )

    assert_rtt_row(output, "N/A")


@pytest.mark.parametrize("compact", [False, True])
def test_unavailable_rtt_is_not_displayed(compact):
    observation = make_observation(
        availability=EvidenceAvailability.UNAVAILABLE,
        value=None,
    )

    output = render_text(
        (observation,),
        compact=compact,
    )

    assert_rtt_row(output, "N/A")


@pytest.mark.parametrize("compact", [False, True])
def test_missing_observation_preserves_na(compact):
    output = render_text(
        (),
        compact=compact,
    )

    assert_rtt_row(output, "N/A")
