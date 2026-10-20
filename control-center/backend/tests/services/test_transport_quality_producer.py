"""Contract RED for normalized MediaMTX SRT transport evidence."""

from datetime import datetime, timezone

from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming.media_observation import EvidenceAvailability
from app.services.transport_quality_producer import (
    TransportQualityProducer,
)


OBSERVED_AT = datetime(
    2026, 10, 20, 12, 0, tzinfo=timezone.utc
)


def make_session(
    *,
    session_id="conn-1",
    role=SessionRole.READER,
    path="ejtv",
):
    return ActiveSession(
        session_id=session_id,
        protocol=SessionProtocol.SRT,
        role=role,
        state="read" if role is SessionRole.READER else "publish",
        remote_ip="203.0.113.10",
        remote_port=9000,
        path=path,
        connected_since=OBSERVED_AT,
    )


def make_snapshot(*sessions):
    return SessionSnapshot(
        captured_at=OBSERVED_AT,
        sessions=tuple(sessions),
    )


def build_observation(
    metrics_text,
    *,
    path_name="ejtv",
    session_snapshot=None,
):
    return TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(metrics_text),
        observed_at=OBSERVED_AT,
        service_id=path_name,
        path_name=path_name,
        source_type="udpSource",
        session_snapshot=session_snapshot,
    )


def test_normalizes_srt_rtt_without_health_evaluation():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 12.5'
    )

    assert observation.service_id == "ejtv"
    assert observation.path_name == "ejtv"
    assert observation.source_type == "udpSource"
    assert observation.observed_at == OBSERVED_AT
    assert observation.availability is EvidenceAvailability.AVAILABLE

    assert len(observation.metrics) == 1

    metric = observation.metrics[0]

    assert metric.metric_name == "srt.connection.rtt"
    assert metric.value == 12.5
    assert metric.unit == "ms"
    assert metric.availability is EvidenceAvailability.AVAILABLE
    assert metric.source == "mediamtx.metrics"
    assert metric.connection_id == "conn-1"
    assert metric.measurement_scope == "CONNECTION"
    assert metric.direction is None


def test_correlates_reader_without_claiming_udp_ingress():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 8',
        session_snapshot=make_snapshot(make_session()),
    )

    assert len(observation.metrics) == 1

    metric = observation.metrics[0]

    assert metric.connection_role is SessionRole.READER
    assert metric.measurement_scope == "CONNECTION"
    assert metric.direction is None


def test_missing_session_does_not_invent_publisher_role():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 9',
        session_snapshot=make_snapshot(),
    )

    assert len(observation.metrics) == 1

    metric = observation.metrics[0]

    assert metric.connection_role is SessionRole.UNKNOWN
    assert metric.measurement_scope == "CONNECTION"
    assert metric.direction is None


def test_other_paths_are_not_mixed():
    observation = build_observation(
        '\n'.join(
            (
                'srt_conns_ms_rtt'
                '{id="conn-1",path="ejtv",state="read"} 10',
                'srt_conns_ms_rtt'
                '{id="conn-2",path="enlace",state="read"} 20',
            )
        )
    )

    assert len(observation.metrics) == 1
    assert observation.metrics[0].connection_id == "conn-1"
    assert observation.metrics[0].value == 10



def test_rejects_contradictory_reader_publisher_role():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 8',
        session_snapshot=make_snapshot(
            make_session(role=SessionRole.PUBLISHER)
        ),
    )

    assert observation.metrics[0].connection_role is SessionRole.UNKNOWN


def test_rejects_contradictory_publisher_reader_role():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="publish"} 8',
        session_snapshot=make_snapshot(
            make_session(role=SessionRole.READER)
        ),
    )

    assert observation.metrics[0].connection_role is SessionRole.UNKNOWN


def test_accepts_matching_publisher_role():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="publish"} 8',
        session_snapshot=make_snapshot(
            make_session(role=SessionRole.PUBLISHER)
        ),
    )

    assert observation.metrics[0].connection_role is SessionRole.PUBLISHER


def test_unknown_prometheus_state_does_not_assign_role():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="unknown"} 8',
        session_snapshot=make_snapshot(make_session()),
    )

    assert observation.metrics[0].connection_role is SessionRole.UNKNOWN



def test_session_publish_state_rejects_prometheus_reader():
    from dataclasses import replace

    session = replace(
        make_session(role=SessionRole.READER),
        state="publish",
    )

    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 8',
        session_snapshot=make_snapshot(session),
    )

    assert observation.metrics[0].connection_role is SessionRole.UNKNOWN


def test_session_read_state_rejects_prometheus_publisher():
    from dataclasses import replace

    session = replace(
        make_session(role=SessionRole.PUBLISHER),
        state="read",
    )

    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="publish"} 8',
        session_snapshot=make_snapshot(session),
    )

    assert observation.metrics[0].connection_role is SessionRole.UNKNOWN


def test_equivalent_reader_states_are_accepted():
    from dataclasses import replace

    session = replace(
        make_session(role=SessionRole.READER),
        state="reading",
    )

    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 8',
        session_snapshot=make_snapshot(session),
    )

    assert observation.metrics[0].connection_role is SessionRole.READER


def test_equivalent_publisher_states_are_accepted():
    from dataclasses import replace

    session = replace(
        make_session(role=SessionRole.PUBLISHER),
        state="publishing",
    )

    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="publish"} 8',
        session_snapshot=make_snapshot(session),
    )

    assert observation.metrics[0].connection_role is SessionRole.PUBLISHER


# ENG-013C — Producer Acquisition Propagation Contract


def make_producer_interval():
    from datetime import timedelta

    from app.domain.streaming.evidence_acquisition_interval import (
        EvidenceAcquisitionInterval,
    )

    return EvidenceAcquisitionInterval(
        started_at=OBSERVED_AT - timedelta(milliseconds=400),
        completed_at=OBSERVED_AT - timedelta(milliseconds=100),
        source="mediamtx.metrics",
    )


def build_with_acquisition_interval(
    metrics_text,
    *,
    acquisition_interval,
    session_snapshot=None,
):
    return TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(metrics_text),
        observed_at=OBSERVED_AT,
        service_id="ejtv",
        path_name="ejtv",
        source_type="udpSource",
        session_snapshot=session_snapshot,
        acquisition_interval=acquisition_interval,
    )


def test_producer_defaults_to_missing_acquisition_interval():
    observation = build_observation(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 12.5'
    )

    assert observation.acquisition_interval is None


def test_producer_preserves_supplied_acquisition_interval():
    interval = make_producer_interval()

    observation = build_with_acquisition_interval(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 12.5',
        acquisition_interval=interval,
    )

    assert observation.acquisition_interval is interval


def test_producer_preserves_interval_when_metrics_unavailable():
    interval = make_producer_interval()

    observation = build_with_acquisition_interval(
        'srt_conns_ms_rtt'
        '{id="other-conn",path="enlace",state="read"} 12.5',
        acquisition_interval=interval,
    )

    assert observation.availability is EvidenceAvailability.UNAVAILABLE
    assert observation.metrics == ()
    assert observation.acquisition_interval is interval


def test_producer_rejects_invalid_acquisition_interval():
    import pytest

    with pytest.raises(TypeError):
        build_with_acquisition_interval(
            'srt_conns_ms_rtt'
        '{id="other-conn",path="enlace",state="read"} 12.5',
            acquisition_interval="invalid",
        )


def test_producer_preserves_srt_reader_identity_with_interval():
    from dataclasses import replace
    from datetime import timedelta

    interval = make_producer_interval()

    # The session must exist before metrics acquisition begins.
    session = replace(
        make_session(),
        connected_since=interval.started_at - timedelta(seconds=1),
    )

    observation = build_with_acquisition_interval(
        'srt_conns_ms_rtt'
        '{id="conn-1",path="ejtv",state="read"} 8',
        acquisition_interval=interval,
        session_snapshot=make_snapshot(session),
    )

    assert len(observation.metrics) == 1
    assert observation.metrics[0].connection_role is SessionRole.READER
    assert observation.metrics[0].measurement_scope == "CONNECTION"
    assert observation.metrics[0].direction is None
    assert observation.acquisition_interval is interval


def test_producer_does_not_replace_observed_at_with_interval():
    interval = make_producer_interval()

    observation = build_with_acquisition_interval(
        'srt_conns_ms_rtt'
        '{id="other-conn",path="enlace",state="read"} 12.5',
        acquisition_interval=interval,
    )

    assert observation.observed_at == OBSERVED_AT
    assert observation.observed_at != interval.completed_at
