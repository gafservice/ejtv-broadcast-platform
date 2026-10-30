"""SRT ingress receive metrics presentation contract.

ENG-013C — 235E.31D.2

Synthetic evidence only. No network or production telemetry.
"""

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


OBSERVED_AT = datetime(
    2026, 10, 29, 12, 0, tzinfo=timezone.utc
)

SOURCE_ID = "srt-publisher-001"


def make_panel():
    row = IncomingRowData(
        path_name="impact",
        source="SRT",
        status="READY",
        bitrate_receive_mbps=6.0,
        health_status=None,
        protocol="SRT",
        transport_source_type="srtConn",
        transport_source_id=SOURCE_ID,
    )

    return IncomingPanelData(
        rows=(row,),
        reference_at=OBSERVED_AT,
    )


def make_metric(
    name,
    value,
    unit,
    *,
    role=SessionRole.PUBLISHER,
    connection_id=SOURCE_ID,
):
    return TransportMetricObservation(
        metric_name=name,
        value=value,
        unit=unit,
        availability=EvidenceAvailability.AVAILABLE,
        source="mediamtx.metrics",
        connection_id=connection_id,
        connection_role=role,
        measurement_scope="CONNECTION",
    )


def make_observation(
    *,
    role=SessionRole.PUBLISHER,
    connection_id=SOURCE_ID,
    source_id=SOURCE_ID,
):
    return TransportQualityObservation(
        service_id="impact",
        path_name="impact",
        source_type="srtConn",
        source_id=source_id,
        observed_at=OBSERVED_AT,
        availability=EvidenceAvailability.AVAILABLE,
        metrics=(
            make_metric(
                "srt.connection.receive.loss_packets",
                7,
                "packets",
                role=role,
                connection_id=connection_id,
            ),
            make_metric(
                "srt.connection.receive.tsbpd_delay",
                120,
                "ms",
                role=role,
                connection_id=connection_id,
            ),
        ),
    )


def render_text(observation, *, compact=False):
    renderer = IncomingTransportCardsRenderer()

    panel = renderer.render(
        make_panel(),
        selected_path_name="impact",
        compact=compact,
        transport_quality_observations=(observation,),
    )

    console = Console(
        width=160,
        force_terminal=False,
        color_system=None,
        record=True,
    )

    console.print(panel)

    return console.export_text()


def assert_field(output, label, expected):
    matching = [
        line
        for line in output.splitlines()
        if label in line
    ]

    assert matching, f"Field not found: {label}"

    assert any(
        expected in line
        for line in matching
    ), (
        f"Expected {label}={expected!r}; "
        f"found {matching!r}"
    )


@pytest.mark.parametrize("compact", [False, True])
def test_publisher_receive_metrics_are_visible(compact):
    output = render_text(
        make_observation(),
        compact=compact,
    )

    assert_field(
        output,
        "Packet Loss",
        "7 packets",
    )

    if not compact:
        assert_field(
            output,
            "Reception Delay",
            "120.00 ms",
        )


@pytest.mark.parametrize(
    "role,connection_id",
    [
        (SessionRole.READER, SOURCE_ID),
        (SessionRole.UNKNOWN, SOURCE_ID),
        (SessionRole.PUBLISHER, "other-connection"),
    ],
)
def test_unattributed_receive_metrics_remain_na(
    role,
    connection_id,
):
    output = render_text(
        make_observation(
            role=role,
            connection_id=connection_id,
        ),
    )

    assert_field(
        output,
        "Packet Loss",
        "N/A",
    )

    assert_field(
        output,
        "Reception Delay",
        "N/A",
    )


def test_missing_source_identity_remains_na():
    output = render_text(
        make_observation(source_id=None),
    )

    assert_field(
        output,
        "Packet Loss",
        "N/A",
    )

    assert_field(
        output,
        "Reception Delay",
        "N/A",
    )


@pytest.mark.parametrize(
    "role,connection_id,source_id,expected",
    [
        (SessionRole.PUBLISHER, SOURCE_ID, SOURCE_ID, "12 packets"),
        (SessionRole.READER, SOURCE_ID, SOURCE_ID, "N/A"),
        (SessionRole.UNKNOWN, SOURCE_ID, SOURCE_ID, "N/A"),
        (SessionRole.PUBLISHER, "other-connection", SOURCE_ID, "N/A"),
        (SessionRole.PUBLISHER, SOURCE_ID, None, "N/A"),
    ],
)
def test_retransmissions_rendered_text_contract(
    role,
    connection_id,
    source_id,
    expected,
):
    """Only attributable ingress retransmissions reach PACKET QUALITY."""

    observation = TransportQualityObservation(
        service_id="impact",
        path_name="impact",
        source_type="srtConn",
        source_id=source_id,
        observed_at=OBSERVED_AT,
        availability=EvidenceAvailability.AVAILABLE,
        metrics=(
            make_metric(
                "srt.connection.receive.retransmitted_packets",
                12,
                "packets",
                role=role,
                connection_id=connection_id,
            ),
        ),
    )

    output = render_text(observation)

    assert_field(output, "Retransmissions", expected)


def test_retransmissions_missing_metric_remains_na():
    """Missing retransmission evidence must not become zero."""

    observation = TransportQualityObservation(
        service_id="impact",
        path_name="impact",
        source_type="srtConn",
        source_id=SOURCE_ID,
        observed_at=OBSERVED_AT,
        availability=EvidenceAvailability.UNAVAILABLE,
        metrics=(),
    )

    output = render_text(observation)

    assert_field(output, "Retransmissions", "N/A")
