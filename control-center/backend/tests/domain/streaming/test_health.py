"""Pruebas de los modelos de salud del streaming."""

from datetime import datetime, timezone

import pytest

from app.domain.streaming.health import (
    HealthStatus,
    SRTConnectionHealth,
    SRTPathHealth,
    StreamingHealth,
)


def build_connection(
    *,
    connection_id: str = "conn-1",
    path_name: str = "enlace",
    status: HealthStatus = HealthStatus.HEALTHY,
) -> SRTConnectionHealth:
    """Construye una conexión válida para las pruebas."""

    return SRTConnectionHealth(
        connection_id=connection_id,
        path_name=path_name,
        state="read",
        rtt_ms=2.5,
        packets_retransmitted=10,
        packets_lost=2,
        status=status,
        message="Conexión estable.",
    )


def test_connection_health_normalizes_text() -> None:
    connection = SRTConnectionHealth(
        connection_id="  conn-1  ",
        path_name="  enlace  ",
        state="  read  ",
        rtt_ms=2.5,
        packets_retransmitted=10,
        packets_lost=2,
        status=HealthStatus.HEALTHY,
        message="  Conexión estable.  ",
    )

    assert connection.connection_id == "conn-1"
    assert connection.path_name == "enlace"
    assert connection.state == "read"
    assert connection.message == "Conexión estable."


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("rtt_ms", -0.1),
        ("packets_retransmitted", -1),
        ("packets_lost", -1),
    ),
)
def test_connection_health_rejects_negative_metrics(
    field_name: str,
    field_value: float | int,
) -> None:
    values = {
        "connection_id": "conn-1",
        "path_name": "enlace",
        "state": "read",
        "rtt_ms": 2.5,
        "packets_retransmitted": 10,
        "packets_lost": 2,
        "status": HealthStatus.HEALTHY,
        "message": "Conexión estable.",
    }

    values[field_name] = field_value

    with pytest.raises(ValueError):
        SRTConnectionHealth(**values)


def test_path_health_counts_connections() -> None:
    path = SRTPathHealth(
        name="enlace",
        connections=(
            build_connection(connection_id="conn-1"),
            build_connection(connection_id="conn-2"),
        ),
        average_rtt_ms=2.5,
        total_packets_retransmitted=20,
        total_packets_lost=4,
        status=HealthStatus.HEALTHY,
        message="Path estable.",
    )

    assert path.connection_count == 2


def test_path_health_rejects_connection_from_another_path() -> None:
    with pytest.raises(
        ValueError,
        match="Todas las conexiones deben pertenecer",
    ):
        SRTPathHealth(
            name="enlace",
            connections=(
                build_connection(path_name="otro-path"),
            ),
            average_rtt_ms=2.5,
            total_packets_retransmitted=10,
            total_packets_lost=2,
            status=HealthStatus.HEALTHY,
            message="Path estable.",
        )


def test_streaming_health_exposes_summary_properties() -> None:
    healthy_path = SRTPathHealth(
        name="enlace",
        connections=(build_connection(),),
        average_rtt_ms=2.5,
        total_packets_retransmitted=10,
        total_packets_lost=2,
        status=HealthStatus.HEALTHY,
        message="Path estable.",
    )

    critical_path = SRTPathHealth(
        name="canal-2",
        connections=(
            build_connection(
                connection_id="conn-2",
                path_name="canal-2",
                status=HealthStatus.CRITICAL,
            ),
        ),
        average_rtt_ms=250.0,
        total_packets_retransmitted=500,
        total_packets_lost=100,
        status=HealthStatus.CRITICAL,
        message="Latencia crítica.",
    )

    health = StreamingHealth(
        captured_at=datetime.now(timezone.utc),
        paths=(healthy_path, critical_path),
        status=HealthStatus.CRITICAL,
        message="Existe al menos un path crítico.",
    )

    assert health.path_count == 2
    assert health.connection_count == 2
    assert health.critical_path_count == 1
    assert health.degraded_path_count == 0
    assert health.get_path("enlace") is healthy_path
    assert health.get_path("inexistente") is None


def test_streaming_health_rejects_duplicate_paths() -> None:
    path = SRTPathHealth(
        name="enlace",
        connections=(build_connection(),),
        average_rtt_ms=2.5,
        total_packets_retransmitted=10,
        total_packets_lost=2,
        status=HealthStatus.HEALTHY,
        message="Path estable.",
    )

    with pytest.raises(
        ValueError,
        match="nombres de paths duplicados",
    ):
        StreamingHealth(
            captured_at=datetime.now(timezone.utc),
            paths=(path, path),
            status=HealthStatus.HEALTHY,
            message="Streaming estable.",
        )


def test_streaming_health_requires_timezone() -> None:
    with pytest.raises(
        ValueError,
        match="zona horaria",
    ):
        StreamingHealth.empty(
            captured_at=datetime.now(),
        )


def test_empty_streaming_health_is_unknown() -> None:
    health = StreamingHealth.empty(
        captured_at=datetime.now(timezone.utc),
    )

    assert health.paths == ()
    assert health.path_count == 0
    assert health.connection_count == 0
    assert health.status is HealthStatus.UNKNOWN
