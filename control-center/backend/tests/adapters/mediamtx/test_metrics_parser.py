"""Pruebas del parser de métricas Prometheus de MediaMTX."""

from __future__ import annotations

import pytest

from app.adapters.mediamtx.exceptions import (
    MediaMTXInvalidResponseError,
)
from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsParser,
)


def build_metrics_text() -> str:
    return """
# Paths
paths{name="ejtv",state="ready"} 1
paths_readers{name="ejtv",readerType="srtConn",state="ready"} 1
paths_inbound_bytes{name="ejtv",state="ready"} 54352423022
paths_outbound_bytes{name="ejtv",state="ready"} 54352403974
paths_inbound_frames_in_error{name="ejtv",state="ready"} 0

# SRT connections
srt_conns_ms_rtt{id="conn-1",path="ejtv",state="read"} 1.5071536886
srt_conns_mbps_send_rate{id="conn-1",path="ejtv",state="read"} 4.1695032858
srt_conns_mbps_link_capacity{id="conn-1",path="ejtv",state="read"} 77.7698974609
srt_conns_packets_retrans{id="conn-1",path="ejtv",state="read"} 223738
srt_conns_packets_send_loss{id="conn-1",path="ejtv",state="read"} 247607
"""


def test_parser_reads_path_metrics() -> None:
    snapshot = MediaMTXMetricsParser().parse(build_metrics_text())

    assert snapshot.get_value(
        "paths",
        name="ejtv",
        state="ready",
    ) == 1.0

    assert snapshot.get_value(
        "paths_readers",
        name="ejtv",
        readerType="srtConn",
        state="ready",
    ) == 1.0

    assert snapshot.get_value(
        "paths_inbound_bytes",
        name="ejtv",
        state="ready",
    ) == 54_352_423_022.0


def test_parser_reads_srt_quality_metrics() -> None:
    snapshot = MediaMTXMetricsParser().parse(build_metrics_text())

    assert snapshot.get_value(
        "srt_conns_ms_rtt",
        path="ejtv",
    ) == pytest.approx(1.5071536886)

    assert snapshot.get_value(
        "srt_conns_mbps_send_rate",
        path="ejtv",
    ) == pytest.approx(4.1695032858)

    assert snapshot.get_value(
        "srt_conns_mbps_link_capacity",
        path="ejtv",
    ) == pytest.approx(77.7698974609)

    assert snapshot.get_value(
        "srt_conns_packets_retrans",
        path="ejtv",
    ) == 223_738.0

    assert snapshot.get_value(
        "srt_conns_packets_send_loss",
        path="ejtv",
    ) == 247_607.0


def test_find_can_return_multiple_connections() -> None:
    metrics = """
srt_conns_ms_rtt{id="conn-1",path="enlace",state="read"} 2.5
srt_conns_ms_rtt{id="conn-2",path="enlace",state="read"} 3.0
"""

    snapshot = MediaMTXMetricsParser().parse(metrics)
    matches = snapshot.find(
        "srt_conns_ms_rtt",
        path="enlace",
    )

    assert len(matches) == 2
    assert {sample.value for sample in matches} == {2.5, 3.0}


def test_get_value_returns_default_when_metric_is_missing() -> None:
    snapshot = MediaMTXMetricsParser().parse(build_metrics_text())

    assert snapshot.get_value(
        "metric_that_does_not_exist",
        default=0.0,
    ) == 0.0


def test_get_value_rejects_ambiguous_result() -> None:
    metrics = """
srt_conns_ms_rtt{id="conn-1",path="enlace"} 2.5
srt_conns_ms_rtt{id="conn-2",path="enlace"} 3.0
"""

    snapshot = MediaMTXMetricsParser().parse(metrics)

    with pytest.raises(MediaMTXInvalidResponseError):
        snapshot.get_value(
            "srt_conns_ms_rtt",
            path="enlace",
        )


@pytest.mark.parametrize(
    "metrics",
    [
        "",
        "# Solo comentarios",
        "métrica inválida",
        'paths{name="ejtv" state="ready"} 1',
    ],
)
def test_parser_rejects_invalid_documents(metrics: str) -> None:
    with pytest.raises(MediaMTXInvalidResponseError):
        MediaMTXMetricsParser().parse(metrics)
