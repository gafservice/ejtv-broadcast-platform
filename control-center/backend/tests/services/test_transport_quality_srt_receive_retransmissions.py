"""SRT received retransmissions normalization contract."""

from datetime import UTC, datetime

import pytest

from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming.media_observation import EvidenceAvailability
from app.services.transport_quality_producer import TransportQualityProducer


OBSERVED_AT = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)

FAMILY = "srt_conns_packets_received_retrans"
NORMALIZED = "srt.connection.receive.retransmitted_packets"


def build(value, *, role=SessionRole.PUBLISHER):
    state = "publish" if role is SessionRole.PUBLISHER else "read"

    metrics_text = (
        f'{FAMILY}'
        f'{{id="conn-1",path="impact",state="{state}"}} '
        f'{value}'
    )

    session = ActiveSession(
        session_id="conn-1",
        protocol=SessionProtocol.SRT,
        role=role,
        state=state,
        remote_ip="203.0.113.10",
        remote_port=9000,
        path="impact",
        connected_since=OBSERVED_AT,
    )

    return TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(metrics_text),
        observed_at=OBSERVED_AT,
        service_id="impact-main",
        path_name="impact",
        source_type="srtConn",
        source_id="conn-1",
        session_snapshot=SessionSnapshot(
            captured_at=OBSERVED_AT,
            sessions=(session,),
        ),
    )


def find_metric(observation):
    return [
        metric
        for metric in observation.metrics
        if metric.metric_name == NORMALIZED
    ]


@pytest.mark.parametrize("value", [0, 1, 17, 250])
def test_normalizes_received_retransmissions(value):
    observation = build(value)

    matches = find_metric(observation)

    assert len(matches) == 1

    metric = matches[0]

    assert metric.value == value
    assert metric.unit == "packets"
    assert metric.availability is EvidenceAvailability.AVAILABLE
    assert metric.connection_id == "conn-1"
    assert metric.connection_role is SessionRole.PUBLISHER
    assert metric.measurement_scope == "CONNECTION"
    assert metric.direction is None
    assert metric.window_seconds is None


@pytest.mark.parametrize("value", [-1, 1.5, "NaN", "+Inf"])
def test_rejects_invalid_received_retransmissions(value):
    observation = build(value)

    assert find_metric(observation) == []


def test_reader_metric_preserves_reader_identity():
    observation = build(9, role=SessionRole.READER)

    matches = find_metric(observation)

    assert len(matches) == 1
    assert matches[0].connection_role is SessionRole.READER
