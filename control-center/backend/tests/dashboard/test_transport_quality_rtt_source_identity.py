"""Conservative source identity attribution for SRT ingress RTT.

ENG-013C — 235E.30A — 9A.68.7D.32D.

A connection RTT candidate is not automatically attributable to ingress.
Only srtConn with explicit matching source/connection IDs may pass
this proposed identity gate. No rendering is authorized here.
"""

from datetime import UTC, datetime

import pytest

from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.sessions.protocol import SessionRole
from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportMetricObservation,
    TransportQualityObservation,
)


OBSERVED_AT = datetime(2026, 10, 20, 19, 0, tzinfo=UTC)


def make_metric(
    *,
    connection_id="publisher-A",
    role=SessionRole.PUBLISHER,
    name="srt.connection.rtt",
    value=12.5,
    unit="ms",
    scope="CONNECTION",
    availability=EvidenceAvailability.AVAILABLE,
):
    return TransportMetricObservation(
        metric_name=name,
        value=value,
        unit=unit,
        availability=availability,
        source="mediamtx.metrics",
        connection_id=connection_id,
        connection_role=role,
        measurement_scope=scope,
    )


def make_observation(
    *,
    source_type="srtConn",
    source_id="publisher-A",
    metrics=None,
    availability=EvidenceAvailability.AVAILABLE,
):
    if metrics is None:
        metrics = (make_metric(),)

    return TransportQualityObservation(
        service_id="impact-main",
        path_name="impact",
        source_type=source_type,
        source_id=source_id,
        observed_at=OBSERVED_AT,
        availability=availability,
        metrics=tuple(metrics),
    )


def select(observation):
    return (
        IncomingTransportCardsRenderer
        ._select_srt_ingress_rtt_attributed(observation)
    )


def test_matching_publisher_source_and_connection_identity():
    candidate = make_metric(connection_id="publisher-A")
    observation = make_observation(
        source_id="publisher-A",
        metrics=(candidate,),
    )

    assert select(observation) is candidate


@pytest.mark.parametrize(
    "source_id,connection_id",
    (
        (None, "publisher-A"),
        ("publisher-A", None),
        (None, None),
        ("publisher-A", "publisher-B"),
        ("publisher-B", "publisher-A"),
    ),
)
def test_rejects_missing_or_mismatched_identity(
    source_id,
    connection_id,
):
    observation = make_observation(
        source_id=source_id,
        metrics=(make_metric(connection_id=connection_id),),
    )

    assert select(observation) is None


@pytest.mark.parametrize(
    "source_type",
    (
        "srtSource",
        "mpegtsSource",
        "udpSource",
        "rtspSource",
        "rtmpConn",
        "hlsSource",
    ),
)
def test_rejects_other_source_types(source_type):
    observation = make_observation(source_type=source_type)

    assert select(observation) is None


@pytest.mark.parametrize(
    "role",
    (
        SessionRole.READER,
        SessionRole.UNKNOWN,
        None,
    ),
)
def test_rejects_non_publisher_connections(role):
    observation = make_observation(
        metrics=(make_metric(role=role),),
    )

    assert select(observation) is None


def test_rejects_ambiguous_publishers():
    observation = make_observation(
        metrics=(
            make_metric(connection_id="publisher-A"),
            make_metric(connection_id="publisher-B"),
        ),
    )

    assert select(observation) is None


def test_reader_does_not_replace_matching_publisher():
    publisher = make_metric(connection_id="publisher-A")
    reader = make_metric(
        connection_id="reader-B",
        role=SessionRole.READER,
    )

    observation = make_observation(
        metrics=(reader, publisher),
    )

    assert select(observation) is publisher


def test_rejects_unknown_connection_alongside_publisher():
    observation = make_observation(
        metrics=(
            make_metric(connection_id="publisher-A"),
            make_metric(
                connection_id="unknown-B",
                role=SessionRole.UNKNOWN,
            ),
        ),
    )

    assert select(observation) is None


def test_rejects_unavailable_observation():
    observation = make_observation(
        availability=EvidenceAvailability.UNAVAILABLE,
    )

    assert select(observation) is None


@pytest.mark.parametrize(
    "name,unit,scope",
    (
        ("other.metric", "ms", "CONNECTION"),
        ("srt.connection.rtt", "s", "CONNECTION"),
        ("srt.connection.rtt", "ms", "SOURCE"),
    ),
)
def test_rejects_invalid_rtt_contract(name, unit, scope):
    observation = make_observation(
        metrics=(
            make_metric(
                name=name,
                unit=unit,
                scope=scope,
            ),
        ),
    )

    assert select(observation) is None
