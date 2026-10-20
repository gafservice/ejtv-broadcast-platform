"""Numeric integrity contract for normalized SRT receive evidence."""

from datetime import UTC, datetime

import pytest

from app.adapters.mediamtx.metrics_parser import MediaMTXMetricsParser
from app.services.transport_quality_producer import TransportQualityProducer


OBSERVED_AT = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

LOSS_FAMILY = "srt_conns_packets_received_loss"
LOSS_NAME = "srt.connection.receive.loss_packets"

DELAY_FAMILY = "srt_conns_ms_receive_tsb_pd_delay"
DELAY_NAME = "srt.connection.receive.tsbpd_delay"


def observe(family, value):
    text = (
        f'{family}'
        '{id="conn-1",path="ejtv",state="read"} '
        f'{value}'
    )

    return TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(text),
        observed_at=OBSERVED_AT,
        service_id="ejtv-main",
        path_name="ejtv",
        source_type="mpegtsSource",
    )


def metric_values(observation, metric_name):
    return [
        metric.value
        for metric in observation.metrics
        if metric.metric_name == metric_name
    ]


@pytest.mark.parametrize(
    "value",
    ("-1", "-0.5", "2.5", "7.25"),
)
def test_rejects_invalid_loss_packet_counts(value):
    observation = observe(LOSS_FAMILY, value)

    assert metric_values(observation, LOSS_NAME) == []


@pytest.mark.parametrize(
    "value",
    ("0", "1", "7", "12.0"),
)
def test_accepts_nonnegative_integer_loss_counts(value):
    observation = observe(LOSS_FAMILY, value)

    assert metric_values(
        observation,
        LOSS_NAME,
    ) == [float(value)]


@pytest.mark.parametrize(
    "value",
    ("-1", "-0.1", "-120"),
)
def test_rejects_negative_receive_tsbpd_delay(value):
    observation = observe(DELAY_FAMILY, value)

    assert metric_values(observation, DELAY_NAME) == []


@pytest.mark.parametrize(
    "value",
    ("0", "0.5", "120", "5000"),
)
def test_accepts_nonnegative_receive_tsbpd_delay(value):
    observation = observe(DELAY_FAMILY, value)

    assert metric_values(
        observation,
        DELAY_NAME,
    ) == [float(value)]


def test_invalid_receive_metric_does_not_remove_valid_rtt():
    text = "\n".join(
        (
            'srt_conns_ms_rtt'
            '{id="conn-1",path="ejtv",state="read"} 12.5',
            f'{LOSS_FAMILY}'
            '{id="conn-1",path="ejtv",state="read"} -1',
        )
    )

    observation = TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(text),
        observed_at=OBSERVED_AT,
        service_id="ejtv-main",
        path_name="ejtv",
        source_type="mpegtsSource",
    )

    assert metric_values(
        observation,
        "srt.connection.rtt",
    ) == [12.5]

    assert metric_values(
        observation,
        LOSS_NAME,
    ) == []


def test_invalid_receive_metric_does_not_remove_valid_tsbpd():
    text = "\n".join(
        (
            f'{LOSS_FAMILY}'
            '{id="conn-1",path="ejtv",state="read"} 2.5',
            f'{DELAY_FAMILY}'
            '{id="conn-1",path="ejtv",state="read"} 120',
        )
    )

    observation = TransportQualityProducer().build(
        snapshot=MediaMTXMetricsParser().parse(text),
        observed_at=OBSERVED_AT,
        service_id="ejtv-main",
        path_name="ejtv",
        source_type="mpegtsSource",
    )

    assert metric_values(observation, LOSS_NAME) == []
    assert metric_values(observation, DELAY_NAME) == [120.0]
