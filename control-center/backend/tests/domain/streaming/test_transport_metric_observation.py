"""ENG-013C — Transport Metric Observation contract RED."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportMetricObservation,
)


def make_metric(**overrides):
    values = {
        "metric_name": "srt.receive.rtt",
        "value": 12.5,
        "unit": "ms",
        "availability": EvidenceAvailability.AVAILABLE,
        "source": "mediamtx.metrics",
        "window_seconds": 10.0,
        "direction": "INGRESS",
        "connection_id": "source-01",
    }
    values.update(overrides)
    return TransportMetricObservation(**values)


def test_preserves_metric_identity_and_evidence():
    metric = make_metric()

    assert metric.metric_name == "srt.receive.rtt"
    assert metric.value == 12.5
    assert metric.unit == "ms"
    assert metric.availability is EvidenceAvailability.AVAILABLE
    assert metric.source == "mediamtx.metrics"
    assert metric.window_seconds == 10.0
    assert metric.direction == "INGRESS"
    assert metric.connection_id == "source-01"


@pytest.mark.parametrize(
    "metric_name",
    [
        "udp.interarrival.variation",
        "srt.receive.rtt",
        "rtmp.connection.reconnects",
        "future.protocol.metric",
    ],
)
def test_accepts_extensible_metric_names(metric_name):
    metric = make_metric(metric_name=metric_name)

    assert metric.metric_name == metric_name


@pytest.mark.parametrize(
    "field_name",
    ["metric_name", "unit", "source"],
)
def test_rejects_blank_required_text(field_name):
    with pytest.raises(ValueError):
        make_metric(**{field_name: "   "})


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), float("-inf")],
)
def test_rejects_non_finite_values(value):
    with pytest.raises(ValueError):
        make_metric(value=value)


def test_available_metric_requires_value():
    with pytest.raises(ValueError):
        make_metric(value=None)


@pytest.mark.parametrize(
    "availability",
    [
        EvidenceAvailability.UNAVAILABLE,
        EvidenceAvailability.INSUFFICIENT,
        EvidenceAvailability.NOT_APPLICABLE,
    ],
)
def test_non_available_metric_has_no_value(availability):
    metric = make_metric(
        availability=availability,
        value=None,
    )

    assert metric.value is None
    assert metric.availability is availability


def test_rejects_value_when_evidence_not_available():
    with pytest.raises(ValueError):
        make_metric(
            availability=EvidenceAvailability.UNAVAILABLE,
            value=12.5,
        )


def test_rejects_non_positive_window():
    with pytest.raises(ValueError):
        make_metric(window_seconds=0)


def test_metric_is_immutable():
    metric = make_metric()

    with pytest.raises(FrozenInstanceError):
        metric.value = 15.0


def test_metric_does_not_assign_health():
    metric = make_metric()

    assert not hasattr(metric, "health")
    assert not hasattr(metric, "status")

# ENG-013C — Transport Metric Provenance Contract


from app.domain.sessions.protocol import SessionRole


def test_provenance_accepts_reader_connection():
    metric = make_metric(
        connection_role=SessionRole.READER,
        measurement_scope="CONNECTION",
    )

    assert metric.connection_role is SessionRole.READER
    assert metric.measurement_scope == "CONNECTION"


def test_provenance_accepts_publisher_connection():
    metric = make_metric(
        connection_role=SessionRole.PUBLISHER,
        measurement_scope="CONNECTION",
    )

    assert metric.connection_role is SessionRole.PUBLISHER
    assert metric.measurement_scope == "CONNECTION"


def test_provenance_accepts_source_scope_without_session():
    metric = make_metric(
        connection_role=None,
        measurement_scope="SOURCE",
        connection_id=None,
    )

    assert metric.connection_role is None
    assert metric.measurement_scope == "SOURCE"
    assert metric.connection_id is None


def test_provenance_defaults_to_unknown_optional_context():
    metric = make_metric()

    assert metric.connection_role is None
    assert metric.measurement_scope is None


@pytest.mark.parametrize(
    "role",
    [
        SessionRole.READER,
        SessionRole.PUBLISHER,
        SessionRole.UNKNOWN,
        None,
    ],
)
def test_provenance_accepts_supported_session_roles(role):
    metric = make_metric(
        connection_role=role,
    )

    assert metric.connection_role is role


@pytest.mark.parametrize(
    "scope",
    [
        "SOURCE",
        "CONNECTION",
        "UNKNOWN",
        None,
    ],
)
def test_provenance_accepts_supported_scopes(scope):
    metric = make_metric(
        measurement_scope=scope,
    )

    assert metric.measurement_scope == scope


def test_provenance_rejects_invalid_session_role():
    with pytest.raises(TypeError):
        make_metric(
            connection_role="READER",
        )


def test_provenance_rejects_invalid_scope():
    with pytest.raises(ValueError):
        make_metric(
            measurement_scope="INVALID",
        )


def test_provenance_does_not_infer_source_from_publisher():
    metric = make_metric(
        connection_role=SessionRole.PUBLISHER,
        measurement_scope="CONNECTION",
    )

    assert metric.measurement_scope == "CONNECTION"


def test_provenance_remains_immutable():
    metric = make_metric(
        connection_role=SessionRole.READER,
        measurement_scope="CONNECTION",
    )

    with pytest.raises(FrozenInstanceError):
        metric.measurement_scope = "SOURCE"
