"""SRT duplicate metric identity isolation contract."""

from datetime import UTC, datetime

import pytest

from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.domain.streaming.media_observation import EvidenceAvailability
from app.services.transport_quality_producer import TransportQualityProducer


OBSERVED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

FAMILIES = (
    ("srt_conns_ms_rtt", "srt.connection.rtt"),
    (
        "srt_conns_packets_received_loss",
        "srt.connection.receive.loss_packets",
    ),
    (
        "srt_conns_ms_receive_tsb_pd_delay",
        "srt.connection.receive.tsbpd_delay",
    ),
)


def sample(family, connection, value, path="ejtv"):
    return (
        f'{family}'
        f'{{id="{connection}",path="{path}",state="read"}} '
        f'{value}'
    )


def observe(*samples):
    return TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(
            "\n".join(samples)
        ),
        observed_at=OBSERVED_AT,
        service_id="ejtv-main",
        path_name="ejtv",
        source_type="mpegtsSource",
    )


def values(observation, metric_name):
    return {
        metric.connection_id: metric.value
        for metric in observation.metrics
        if metric.metric_name == metric_name
    }


@pytest.mark.parametrize("family,normalized", FAMILIES)
def test_duplicate_same_value_does_not_invalidate_other_connection(
    family,
    normalized,
):
    observation = observe(
        sample(family, "reader-A", 3),
        sample(family, "reader-A", 3),
        sample(family, "reader-B", 7),
    )

    assert values(observation, normalized) == {
        "reader-B": 7.0,
    }


@pytest.mark.parametrize("family,normalized", FAMILIES)
def test_duplicate_conflicting_values_are_not_arbitrarily_selected(
    family,
    normalized,
):
    observation = observe(
        sample(family, "reader-A", 3),
        sample(family, "reader-A", 9),
        sample(family, "reader-B", 7),
    )

    assert values(observation, normalized) == {
        "reader-B": 7.0,
    }


@pytest.mark.parametrize("family,normalized", FAMILIES)
def test_only_duplicate_identity_is_removed(
    family,
    normalized,
):
    observation = observe(
        sample(family, "reader-A", 3),
        sample(family, "reader-A", 9),
        sample(family, "reader-B", 7),
        sample(
            "srt_conns_packets_received_loss"
            if family != "srt_conns_packets_received_loss"
            else "srt_conns_ms_rtt",
            "reader-A",
            2,
        ),
    )

    assert values(observation, normalized) == {
        "reader-B": 7.0,
    }

    assert len(observation.metrics) == 2


@pytest.mark.parametrize("family,normalized", FAMILIES)
def test_independent_connections_are_preserved(
    family,
    normalized,
):
    observation = observe(
        sample(family, "reader-A", 3),
        sample(family, "reader-B", 7),
    )

    assert values(observation, normalized) == {
        "reader-A": 3.0,
        "reader-B": 7.0,
    }


def test_all_duplicate_identities_produce_unavailable_observation():
    observation = observe(
        sample("srt_conns_packets_received_loss", "reader-A", 3),
        sample("srt_conns_packets_received_loss", "reader-A", 9),
    )

    assert observation.metrics == ()
    assert observation.availability is EvidenceAvailability.UNAVAILABLE


def test_duplicate_rtt_does_not_remove_valid_receive_loss():
    observation = observe(
        sample("srt_conns_ms_rtt", "reader-A", 10),
        sample("srt_conns_ms_rtt", "reader-A", 20),
        sample("srt_conns_packets_received_loss", "reader-A", 3),
    )

    assert values(observation, "srt.connection.rtt") == {}
    assert values(
        observation,
        "srt.connection.receive.loss_packets",
    ) == {"reader-A": 3.0}
