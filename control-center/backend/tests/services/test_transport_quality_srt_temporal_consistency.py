"""Temporal consistency of SRT session-role attribution."""

from datetime import UTC, datetime, timedelta

import pytest

from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming.evidence_acquisition_interval import (
    EvidenceAcquisitionInterval,
)
from app.domain.streaming.media_observation import EvidenceAvailability
from app.services.transport_quality_producer import TransportQualityProducer


BASE = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

FAMILIES = (
    ("srt_conns_ms_rtt", "srt.connection.rtt", 12.0),
    (
        "srt_conns_packets_received_loss",
        "srt.connection.receive.loss_packets",
        3.0,
    ),
    (
        "srt_conns_ms_receive_tsb_pd_delay",
        "srt.connection.receive.tsbpd_delay",
        120.0,
    ),
)


def make_interval():
    return EvidenceAcquisitionInterval(
        started_at=BASE,
        completed_at=BASE + timedelta(milliseconds=100),
        source="mediamtx.metrics",
    )


def observe(
    family,
    value,
    *,
    role=SessionRole.READER,
    connected_since=None,
    captured_at=None,
    acquisition_interval=None,
    connection_id="conn-1",
    session_id="conn-1",
):
    state = (
        "read"
        if role is SessionRole.READER
        else "publish"
    )

    metrics = MediaMTXMetricsParser().parse(
        f'{family}'
        f'{{id="{connection_id}",path="ejtv",state="{state}"}} '
        f'{value}'
    )

    session = ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state=state,
        remote_ip="203.0.113.10",
        remote_port=9000,
        path="ejtv",
        connected_since=(
            connected_since
            if connected_since is not None
            else BASE - timedelta(minutes=1)
        ),
    )

    sessions = SessionSnapshot(
        captured_at=(
            captured_at
            if captured_at is not None
            else BASE
        ),
        sessions=(session,),
    )

    return TransportQualityProducer().build(
        snapshot=metrics,
        observed_at=BASE,
        service_id="ejtv-main",
        path_name="ejtv",
        source_type="mpegtsSource",
        session_snapshot=sessions,
        acquisition_interval=acquisition_interval,
    )


@pytest.mark.parametrize(
    "family,metric_name,value",
    FAMILIES,
)
@pytest.mark.parametrize(
    "role",
    (SessionRole.READER, SessionRole.PUBLISHER),
)
def test_connection_created_after_acquisition_is_unknown(
    family,
    metric_name,
    value,
    role,
):
    interval = make_interval()

    observation = observe(
        family,
        value,
        role=role,
        connected_since=interval.completed_at
        + timedelta(microseconds=1),
        captured_at=interval.completed_at
        + timedelta(seconds=10),
        acquisition_interval=interval,
    )

    assert len(observation.metrics) == 1

    metric = observation.metrics[0]

    assert metric.metric_name == metric_name
    assert metric.value == value
    assert metric.connection_id == "conn-1"
    assert metric.connection_role is SessionRole.UNKNOWN
    assert metric.availability is EvidenceAvailability.AVAILABLE


@pytest.mark.parametrize(
    "family,metric_name,value",
    FAMILIES,
)
@pytest.mark.parametrize(
    "role",
    (SessionRole.READER, SessionRole.PUBLISHER),
)
def test_connection_created_at_acquisition_end_is_preserved(
    family,
    metric_name,
    value,
    role,
):
    interval = make_interval()

    observation = observe(
        family,
        value,
        role=role,
        connected_since=interval.completed_at,
        captured_at=interval.completed_at,
        acquisition_interval=interval,
    )

    assert len(observation.metrics) == 1
    assert observation.metrics[0].metric_name == metric_name
    assert observation.metrics[0].connection_role is role


@pytest.mark.parametrize(
    "family,metric_name,value",
    FAMILIES,
)
@pytest.mark.parametrize(
    "role",
    (SessionRole.READER, SessionRole.PUBLISHER),
)
def test_connection_created_before_acquisition_is_preserved(
    family,
    metric_name,
    value,
    role,
):
    interval = make_interval()

    observation = observe(
        family,
        value,
        role=role,
        connected_since=interval.started_at
        - timedelta(seconds=30),
        acquisition_interval=interval,
    )

    assert len(observation.metrics) == 1
    assert observation.metrics[0].metric_name == metric_name
    assert observation.metrics[0].connection_role is role


@pytest.mark.parametrize(
    "family,metric_name,value",
    FAMILIES,
)
@pytest.mark.parametrize(
    "role",
    (SessionRole.READER, SessionRole.PUBLISHER),
)
def test_missing_interval_preserves_legacy_role(
    family,
    metric_name,
    value,
    role,
):
    observation = observe(
        family,
        value,
        role=role,
        connected_since=BASE + timedelta(seconds=30),
        acquisition_interval=None,
    )

    assert len(observation.metrics) == 1
    assert observation.metrics[0].metric_name == metric_name
    assert observation.metrics[0].connection_role is role


@pytest.mark.parametrize(
    "family,metric_name,value",
    FAMILIES,
)
def test_unmatched_session_remains_unknown(
    family,
    metric_name,
    value,
):
    observation = observe(
        family,
        value,
        session_id="other-connection",
        acquisition_interval=make_interval(),
    )

    assert len(observation.metrics) == 1
    assert observation.metrics[0].metric_name == metric_name
    assert observation.metrics[0].connection_role is SessionRole.UNKNOWN


def test_temporal_rejection_preserves_observation_interval():
    interval = make_interval()

    observation = observe(
        "srt_conns_ms_rtt",
        12,
        connected_since=interval.completed_at
        + timedelta(seconds=5),
        acquisition_interval=interval,
    )

    assert observation.acquisition_interval is interval
    assert observation.observed_at == BASE
    assert observation.availability is EvidenceAvailability.AVAILABLE
    assert len(observation.metrics) == 1
    assert observation.metrics[0].connection_role is SessionRole.UNKNOWN
