"""ENG-013C — Transport Quality Observation contract RED."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)


OBSERVED_AT = datetime(
    2026, 10, 20, 15, 0, tzinfo=timezone.utc
)


def make_observation(**overrides):
    values = {
        "service_id": "impact",
        "path_name": "impact",
        "source_type": "srtSource",
        "observed_at": OBSERVED_AT,
        "availability": EvidenceAvailability.AVAILABLE,
    }
    values.update(overrides)
    return TransportQualityObservation(**values)


def test_preserves_transport_observation_identity():
    observation = make_observation()

    assert observation.service_id == "impact"
    assert observation.path_name == "impact"
    assert observation.source_type == "srtSource"
    assert observation.observed_at == OBSERVED_AT
    assert observation.availability is EvidenceAvailability.AVAILABLE


@pytest.mark.parametrize(
    "source_type",
    [
        "srtSource",
        "udpSource",
        "rtmpSource",
        "rtspSource",
        "futureSource",
    ],
)
def test_accepts_extensible_source_types(source_type):
    observation = make_observation(source_type=source_type)

    assert observation.source_type == source_type


def test_rejects_naive_observation_timestamp():
    with pytest.raises(ValueError):
        make_observation(
            observed_at=datetime(2026, 10, 20, 15, 0)
        )


def test_rejects_invalid_availability():
    with pytest.raises(TypeError):
        make_observation(availability="available")


def test_observation_is_immutable():
    observation = make_observation()

    with pytest.raises(FrozenInstanceError):
        observation.service_id = "ejtv"


def test_observation_does_not_assign_health():
    observation = make_observation()

    assert not hasattr(observation, "health")
    assert not hasattr(observation, "status")


# ENG-013C — Transport Quality Metric Collection Contract


def make_metric(
    metric_name: str,
    *,
    direction: str = "INGRESS",
    connection_id: str = "source-01",
):
    from app.domain.streaming.transport_quality_observation import (
        TransportMetricObservation,
    )

    return TransportMetricObservation(
        metric_name=metric_name,
        value=12.5,
        unit="ms",
        availability=EvidenceAvailability.AVAILABLE,
        source="mediamtx.metrics",
        window_seconds=10.0,
        direction=direction,
        connection_id=connection_id,
    )


def test_observation_accepts_multiple_metrics():
    rtt = make_metric("srt.receive.rtt")
    delay = make_metric("srt.receive.delay")

    observation = make_observation(
        metrics=(rtt, delay),
    )

    assert observation.metrics == (rtt, delay)


def test_observation_defaults_to_empty_metric_collection():
    observation = make_observation()

    assert observation.metrics == ()


def test_observation_rejects_mutable_metric_collection():
    with pytest.raises(TypeError):
        make_observation(
            metrics=[make_metric("srt.receive.rtt")],
        )


def test_observation_rejects_invalid_metric_elements():
    with pytest.raises(TypeError):
        make_observation(
            metrics=("invalid-metric",),
        )


def test_observation_rejects_duplicate_metric_identity():
    metric = make_metric("srt.receive.rtt")

    with pytest.raises(ValueError):
        make_observation(
            metrics=(metric, metric),
        )


def test_observation_allows_same_metric_on_distinct_connections():
    first = make_metric(
        "srt.receive.rtt",
        connection_id="source-01",
    )
    second = make_metric(
        "srt.receive.rtt",
        connection_id="source-02",
    )

    observation = make_observation(
        metrics=(first, second),
    )

    assert observation.metrics == (first, second)


def test_observation_metric_collection_is_immutable():
    observation = make_observation(
        metrics=(make_metric("srt.receive.rtt"),),
    )

    with pytest.raises(FrozenInstanceError):
        observation.metrics = ()

# ENG-013C — Transport Metric Provenance Identity Contract


def test_identity_distinguishes_measurement_scope():
    from app.domain.streaming.transport_quality_observation import (
        TransportMetricObservation,
    )

    from app.domain.sessions.protocol import SessionRole

    common = dict(
        metric_name="transport.packet_loss",
        value=0.0,
        unit="packets",
        availability=EvidenceAvailability.AVAILABLE,
        source="mediamtx.metrics",
        window_seconds=10.0,
        direction="INGRESS",
        connection_id="connection-01",
        connection_role=SessionRole.PUBLISHER,
    )

    source_metric = TransportMetricObservation(
        **common,
        measurement_scope="SOURCE",
    )

    connection_metric = TransportMetricObservation(
        **common,
        measurement_scope="CONNECTION",
    )

    observation = make_observation(
        metrics=(source_metric, connection_metric),
    )

    assert observation.metrics == (
        source_metric,
        connection_metric,
    )


def test_identity_distinguishes_connection_role():
    from app.domain.streaming.transport_quality_observation import (
        TransportMetricObservation,
    )

    from app.domain.sessions.protocol import SessionRole

    common = dict(
        metric_name="srt.connection.rtt",
        value=12.5,
        unit="ms",
        availability=EvidenceAvailability.AVAILABLE,
        source="mediamtx.metrics",
        window_seconds=10.0,
        direction="INGRESS",
        connection_id="connection-01",
        measurement_scope="CONNECTION",
    )

    reader_metric = TransportMetricObservation(
        **common,
        connection_role=SessionRole.READER,
    )

    publisher_metric = TransportMetricObservation(
        **common,
        connection_role=SessionRole.PUBLISHER,
    )

    observation = make_observation(
        metrics=(reader_metric, publisher_metric),
    )

    assert observation.metrics == (
        reader_metric,
        publisher_metric,
    )


def test_identity_still_rejects_exact_provenance_duplicates():
    from app.domain.streaming.transport_quality_observation import (
        TransportMetricObservation,
    )

    from app.domain.sessions.protocol import SessionRole

    common = dict(
        metric_name="srt.connection.rtt",
        value=12.5,
        unit="ms",
        availability=EvidenceAvailability.AVAILABLE,
        source="mediamtx.metrics",
        window_seconds=10.0,
        direction="INGRESS",
        connection_id="connection-01",
        connection_role=SessionRole.READER,
        measurement_scope="CONNECTION",
    )

    first = TransportMetricObservation(**common)
    second = TransportMetricObservation(**common)

    with pytest.raises(ValueError):
        make_observation(
            metrics=(first, second),
        )



# ENG-013C — Transport Acquisition Provenance Contract


def make_acquisition_interval(
    *,
    started_at=None,
    completed_at=None,
    source="mediamtx.metrics",
):
    from datetime import timedelta

    from app.domain.streaming.evidence_acquisition_interval import (
        EvidenceAcquisitionInterval,
    )

    if started_at is None:
        started_at = OBSERVED_AT - timedelta(seconds=2)

    if completed_at is None:
        completed_at = started_at + timedelta(milliseconds=250)

    return EvidenceAcquisitionInterval(
        started_at=started_at,
        completed_at=completed_at,
        source=source,
    )


def test_acquisition_interval_defaults_to_none():
    observation = make_observation()

    assert observation.acquisition_interval is None


def test_acquisition_interval_preserves_valid_evidence():
    interval = make_acquisition_interval()

    observation = make_observation(
        acquisition_interval=interval,
    )

    assert observation.acquisition_interval is interval


def test_acquisition_interval_rejects_invalid_type():
    with pytest.raises(TypeError):
        make_observation(
            acquisition_interval="invalid",
        )


def test_acquisition_interval_allows_observation_before_acquisition():
    from datetime import timedelta

    interval = make_acquisition_interval(
        started_at=OBSERVED_AT + timedelta(seconds=5),
    )

    observation = make_observation(
        acquisition_interval=interval,
    )

    assert observation.observed_at < interval.started_at


def test_acquisition_interval_allows_observation_after_acquisition():
    interval = make_acquisition_interval()

    observation = make_observation(
        acquisition_interval=interval,
    )

    assert observation.observed_at > interval.completed_at


def test_acquisition_interval_preserves_source_provenance():
    interval = make_acquisition_interval(
        source="packet.analyzer",
    )

    observation = make_observation(
        acquisition_interval=interval,
    )

    assert observation.acquisition_interval.source == "packet.analyzer"


def test_acquisition_interval_is_immutable():
    interval = make_acquisition_interval()

    observation = make_observation(
        acquisition_interval=interval,
    )

    with pytest.raises(FrozenInstanceError):
        observation.acquisition_interval = None
