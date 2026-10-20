"""Source identity propagation contract for TransportQualityProducer."""

from datetime import UTC, datetime

import pytest

from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.domain.streaming.media_observation import EvidenceAvailability
from app.services.transport_quality_producer import TransportQualityProducer


OBSERVED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def make_observation(*, source_type="srtConn", source_id=None):
    snapshot = MediaMTXMetricsParser().parse(
        'srt_conns_ms_rtt'
        '{id="reader-1",path="impact",state="read"} 12.5'
    )

    return TransportQualityProducer().build(
        snapshot=snapshot,
        observed_at=OBSERVED_AT,
        service_id="impact-main",
        path_name="impact",
        source_type=source_type,
        source_id=source_id,
    )


def test_preserves_srt_source_identity():
    observation = make_observation(source_id="publisher-A")

    assert observation.source_id == "publisher-A"


def test_preserves_udp_source_identity():
    observation = make_observation(
        source_type="udpSource",
        source_id="udp-source-1",
    )

    assert observation.source_id == "udp-source-1"


def test_accepts_explicit_missing_identity():
    observation = make_observation(source_id=None)

    assert observation.source_id is None


def test_normalizes_source_identity():
    observation = make_observation(source_id=" publisher-A ")

    assert observation.source_id == "publisher-A"


@pytest.mark.parametrize("invalid", ("", " ", "\t"))
def test_rejects_blank_source_identity(invalid):
    with pytest.raises(ValueError, match="source_id"):
        make_observation(source_id=invalid)


@pytest.mark.parametrize("invalid", (123, True, [], {}))
def test_rejects_invalid_source_identity_type(invalid):
    with pytest.raises(TypeError, match="source_id must be a str"):
        make_observation(source_id=invalid)


def test_reader_connection_id_is_not_source_identity():
    observation = make_observation(
        source_type="udpSource",
        source_id="udp-source-1",
    )

    assert observation.source_id == "udp-source-1"

    assert observation.availability is EvidenceAvailability.AVAILABLE

    assert len(observation.metrics) == 1

    metric = observation.metrics[0]

    assert metric.connection_id == "reader-1"
    assert metric.connection_id != observation.source_id
