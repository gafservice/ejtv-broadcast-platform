"""Conservative SRT ingress RTT candidate selection.

ENG-013C — 235E.30A — 9A.68.7D.13.

This contract identifies a candidate metric only.
It does not prove source-ingress attribution or authorize rendering.
"""

from datetime import datetime, timezone

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


OBSERVED_AT = datetime(
    2026, 10, 20, 19, 0, tzinfo=timezone.utc
)


def metric(
    *,
    name="srt.connection.rtt",
    value=12.5,
    unit="ms",
    availability=EvidenceAvailability.AVAILABLE,
    role=SessionRole.PUBLISHER,
    scope="CONNECTION",
    connection_id="publisher-1",
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


def observation(
    source_type="srtConn",
    metrics=(),
    availability=EvidenceAvailability.AVAILABLE,
):
    return TransportQualityObservation(
        service_id="impact",
        path_name="impact",
        source_type=source_type,
        observed_at=OBSERVED_AT,
        availability=availability,
        metrics=tuple(metrics),
    )


def select(item):
    return (
        IncomingTransportCardsRenderer
        ._select_srt_ingress_rtt_candidate(item)
    )


def test_unique_publisher_rtt_is_candidate_only():
    candidate = metric()
    result = select(observation(metrics=(candidate,)))
    assert result is candidate


@pytest.mark.parametrize(
    "source_type",
    ("udpSource", "rtspSource", "hlsSource"),
)
def test_rejects_non_srt_ingress_sources(source_type):
    result = select(
        observation(
            source_type=source_type,
            metrics=(metric(),),
        )
    )
    assert result is None


@pytest.mark.parametrize(
    "role",
    (SessionRole.READER, SessionRole.UNKNOWN, None),
)
def test_rejects_non_publisher_roles(role):
    result = select(
        observation(metrics=(metric(role=role),))
    )
    assert result is None


@pytest.mark.parametrize(
    "name,unit,scope",
    (
        ("srt.connection.send_loss", "ms", "CONNECTION"),
        ("srt.connection.rtt", "s", "CONNECTION"),
        ("srt.connection.rtt", "ms", "SOURCE"),
        ("srt.connection.rtt", "ms", "UNKNOWN"),
        ("srt.connection.rtt", "ms", None),
    ),
)
def test_rejects_wrong_metric_contract(name, unit, scope):
    result = select(
        observation(
            metrics=(
                metric(
                    name=name,
                    unit=unit,
                    scope=scope,
                ),
            )
        )
    )
    assert result is None


def test_rejects_unavailable_observation():
    result = select(
        observation(
            availability=EvidenceAvailability.UNAVAILABLE,
            metrics=(metric(),),
        )
    )
    assert result is None


def test_rejects_unavailable_metric():
    unavailable = metric(
        value=None,
        availability=EvidenceAvailability.UNAVAILABLE,
    )
    result = select(
        observation(metrics=(unavailable,))
    )
    assert result is None


def test_rejects_multiple_publisher_connections():
    result = select(
        observation(
            metrics=(
                metric(connection_id="publisher-1"),
                metric(connection_id="publisher-2"),
            )
        )
    )
    assert result is None


def test_rejects_missing_connection_identity():
    result = select(
        observation(
            metrics=(metric(connection_id=None),)
        )
    )
    assert result is None


def test_rejects_unknown_connection_alongside_publisher():
    result = select(
        observation(
            metrics=(
                metric(connection_id="publisher-1"),
                metric(
                    role=SessionRole.UNKNOWN,
                    connection_id="unresolved-1",
                ),
            )
        )
    )
    assert result is None


def test_reader_connection_does_not_block_unique_publisher():
    publisher = metric(connection_id="publisher-1")
    reader = metric(
        role=SessionRole.READER,
        connection_id="reader-1",
    )

    result = select(
        observation(metrics=(reader, publisher))
    )

    assert result is publisher


def test_empty_observation_has_no_candidate():
    result = select(observation(metrics=()))
    assert result is None
