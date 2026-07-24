"""Pruebas del servicio de salud del streaming."""

from datetime import datetime, timezone

import pytest

from app.adapters.mediamtx.metrics_parser import (
    MediaMTXMetricsParser,
)
from app.domain.streaming import HealthStatus
from app.services.streaming_health_service import (
    StreamingHealthService,
)


CAPTURED_AT = datetime(
    2026,
    7,
    22,
    12,
    0,
    tzinfo=timezone.utc,
)


def build_health(metrics: str):
    """Procesa métricas y construye StreamingHealth."""

    snapshot = MediaMTXMetricsParser().parse(metrics)

    return StreamingHealthService().build(
        snapshot=snapshot,
        captured_at=CAPTURED_AT,
    )


def test_builds_healthy_connection() -> None:
    health = build_health(
        """
srt_conns_ms_rtt{id="conn-1",path="enlace",state="read"} 2.5
srt_conns_mbps_send_rate{id="conn-1",path="enlace",state="read"} 4
srt_conns_mbps_link_capacity{id="conn-1",path="enlace",state="read"} 80
srt_conns_packets_retrans{id="conn-1",path="enlace",state="read"} 10
srt_conns_packets_send_loss{id="conn-1",path="enlace",state="read"} 2
"""
    )

    connection = health.paths[0].connections[0]

    assert health.status is HealthStatus.HEALTHY
    assert connection.status is HealthStatus.HEALTHY
    assert connection.rtt_ms == pytest.approx(2.5)
    assert connection.link_utilization_percent == pytest.approx(5.0)
    assert connection.packets_retransmitted == 10
    assert connection.packets_lost == 2


def test_classifies_degraded_rtt() -> None:
    health = build_health(
        """
srt_conns_ms_rtt{id="conn-1",path="enlace",state="read"} 150
"""
    )

    assert health.status is HealthStatus.DEGRADED
    assert (
        health.paths[0].connections[0].status
        is HealthStatus.DEGRADED
    )


def test_classifies_critical_rtt() -> None:
    health = build_health(
        """
srt_conns_ms_rtt{id="conn-1",path="enlace",state="read"} 300
"""
    )

    assert health.status is HealthStatus.CRITICAL


def test_classifies_critical_link_utilization() -> None:
    health = build_health(
        """
srt_conns_ms_rtt{id="conn-1",path="enlace",state="read"} 2
srt_conns_mbps_send_rate{id="conn-1",path="enlace",state="read"} 95
srt_conns_mbps_link_capacity{id="conn-1",path="enlace",state="read"} 100
"""
    )

    connection = health.paths[0].connections[0]

    assert connection.link_utilization_percent == pytest.approx(95)
    assert connection.status is HealthStatus.CRITICAL
    assert health.status is HealthStatus.CRITICAL


def test_aggregates_multiple_connections_by_path() -> None:
    health = build_health(
        """
srt_conns_ms_rtt{id="conn-1",path="enlace",state="read"} 10
srt_conns_ms_rtt{id="conn-2",path="enlace",state="read"} 30
srt_conns_packets_retrans{id="conn-1",path="enlace",state="read"} 5
srt_conns_packets_retrans{id="conn-2",path="enlace",state="read"} 7
srt_conns_packets_send_loss{id="conn-1",path="enlace",state="read"} 2
srt_conns_packets_send_loss{id="conn-2",path="enlace",state="read"} 3
"""
    )

    path = health.get_path("enlace")

    assert path is not None
    assert path.connection_count == 2
    assert path.average_rtt_ms == pytest.approx(20)
    assert path.maximum_rtt_ms == pytest.approx(30)
    assert path.total_packets_retransmitted == 12
    assert path.total_packets_lost == 5


def test_worst_connection_determines_path_status() -> None:
    health = build_health(
        """
srt_conns_ms_rtt{id="conn-1",path="enlace",state="read"} 10
srt_conns_ms_rtt{id="conn-2",path="enlace",state="read"} 300
"""
    )

    path = health.get_path("enlace")

    assert path is not None
    assert path.status is HealthStatus.CRITICAL
    assert health.status is HealthStatus.CRITICAL


def test_unrelated_metrics_return_unknown_health() -> None:
    health = build_health(
        """
paths{name="enlace",state="ready"} 1
"""
    )

    assert health.paths == ()
    assert health.status is HealthStatus.UNKNOWN


def test_zero_capacity_does_not_divide_by_zero() -> None:
    health = build_health(
        """
srt_conns_mbps_send_rate{id="conn-1",path="enlace"} 4
srt_conns_mbps_link_capacity{id="conn-1",path="enlace"} 0
"""
    )

    connection = health.paths[0].connections[0]

    assert connection.link_utilization_percent is None
    assert connection.status is HealthStatus.UNKNOWN


def test_samples_without_connection_identity_are_ignored() -> None:
    health = build_health(
        """
srt_conns_ms_rtt{path="enlace"} 2.5
"""
    )

    assert health.paths == ()
    assert health.status is HealthStatus.UNKNOWN
