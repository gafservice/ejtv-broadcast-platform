"""SRT receive-quality evidence normalization contract.

ENG-013C — 235E.30A — 9A.68.7D.33C.

These are connection-scoped observations, not ingress Health
conclusions or dashboard display authorization.
"""

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


OBSERVED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

METRIC_CASES = (
    (
        "srt_conns_packets_received_loss",
        "srt.connection.receive.loss_packets",
        "packets",
        7,
    ),
    (
        "srt_conns_ms_receive_tsb_pd_delay",
        "srt.connection.receive.tsbpd_delay",
        "ms",
        120,
    ),
)


def make_session(
    *,
    session_id="conn-1",
    path="ejtv",
    role=SessionRole.READER,
):
    state = (
        "read"
        if role is SessionRole.READER
        else "publish"
    )

    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state=state,
        remote_ip="203.0.113.10",
        remote_port=9000,
        path=path,
        connected_since=OBSERVED_AT,
    )


def build(
    metrics_text,
    *,
    path_name="ejtv",
    sessions=(),
    source_type="mpegtsSource",
):
    return TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(metrics_text),
        observed_at=OBSERVED_AT,
        service_id=f"{path_name}-main",
        path_name=path_name,
        source_type=source_type,
        session_snapshot=SessionSnapshot(
            captured_at=OBSERVED_AT,
            sessions=tuple(sessions),
        ),
    )


def sample(family, *, path="ejtv", state="read", connection="conn-1", value=7):
    return (
        f'{family}'
        f'{{id="{connection}",path="{path}",state="{state}"}} '
        f'{value}'
    )


@pytest.mark.parametrize(
    "family,normalized,unit,value",
    METRIC_CASES,
)
def test_normalizes_connection_scoped_receive_metric(
    family,
    normalized,
    unit,
    value,
):
    observation = build(
        sample(family, value=value),
        sessions=(make_session(),),
    )

    matching = [
        metric
        for metric in observation.metrics
        if metric.metric_name == normalized
    ]

    assert len(matching) == 1

    metric = matching[0]

    assert metric.value == value
    assert metric.unit == unit
    assert metric.availability is EvidenceAvailability.AVAILABLE
    assert metric.source == "mediamtx.metrics"
    assert metric.connection_id == "conn-1"
    assert metric.connection_role is SessionRole.READER
    assert metric.measurement_scope == "CONNECTION"
    assert metric.direction is None
    assert metric.window_seconds is None


@pytest.mark.parametrize(
    "family,normalized,unit,value",
    METRIC_CASES,
)
def test_rejects_other_path(
    family,
    normalized,
    unit,
    value,
):
    observation = build(
        sample(family, path="enlace", value=value),
        sessions=(make_session(),),
    )

    assert not any(
        metric.metric_name == normalized
        for metric in observation.metrics
    )


@pytest.mark.parametrize(
    "family,normalized,unit,value",
    METRIC_CASES,
)
def test_unknown_role_when_session_missing(
    family,
    normalized,
    unit,
    value,
):
    observation = build(
        sample(family, value=value),
    )

    matching = [
        metric
        for metric in observation.metrics
        if metric.metric_name == normalized
    ]

    assert len(matching) == 1
    assert matching[0].connection_role is SessionRole.UNKNOWN


@pytest.mark.parametrize(
    "family,normalized,unit,value",
    METRIC_CASES,
)
def test_rejects_contradictory_session_role(
    family,
    normalized,
    unit,
    value,
):
    observation = build(
        sample(family, state="read", value=value),
        sessions=(
            make_session(role=SessionRole.PUBLISHER),
        ),
    )

    matching = [
        metric
        for metric in observation.metrics
        if metric.metric_name == normalized
    ]

    assert len(matching) == 1
    assert matching[0].connection_role is SessionRole.UNKNOWN


def test_multiple_receive_metrics_keep_connection_identity():
    observation = build(
        "\n".join(
            (
                sample(
                    "srt_conns_packets_received_loss",
                    value=3,
                ),
                sample(
                    "srt_conns_ms_receive_tsb_pd_delay",
                    value=120,
                ),
            )
        ),
        sessions=(make_session(),),
    )

    names = {
        metric.metric_name
        for metric in observation.metrics
    }

    assert "srt.connection.receive.loss_packets" in names
    assert "srt.connection.receive.tsbpd_delay" in names

    receive_metrics = [
        metric
        for metric in observation.metrics
        if metric.metric_name.startswith("srt.connection.receive.")
    ]

    assert len(receive_metrics) == 2
    assert all(
        metric.connection_id == "conn-1"
        for metric in receive_metrics
    )


def test_reader_metrics_do_not_claim_udp_ingress():
    observation = build(
        sample(
            "srt_conns_packets_received_loss",
            value=5,
        ),
        sessions=(make_session(),),
        source_type="mpegtsSource",
    )

    assert observation.source_type == "mpegtsSource"

    metric = next(
        metric
        for metric in observation.metrics
        if metric.metric_name == "srt.connection.receive.loss_packets"
    )

    assert metric.connection_role is SessionRole.READER
    assert metric.measurement_scope == "CONNECTION"
    assert metric.direction is None
