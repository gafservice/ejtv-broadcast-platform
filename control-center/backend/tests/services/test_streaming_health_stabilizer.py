from datetime import UTC, datetime, timedelta

from app.domain.streaming.health import (
    HealthStatus,
    SRTConnectionHealth,
    SRTPathHealth,
    StreamingHealth,
)
from app.services.srt_connection_health_stabilizer import (
    SRTConnectionHealthStabilizer,
)
from app.services.streaming_health_stabilizer import (
    StreamingHealthStabilizer,
)


BASE_TIME = datetime(
    2026,
    9,
    6,
    12,
    0,
    tzinfo=UTC,
)


def make_health(
    *,
    captured_at: datetime,
    status: HealthStatus,
    rtt_ms: float,
    message: str,
) -> StreamingHealth:
    connection = SRTConnectionHealth(
        connection_id="conn-1",
        path_name="impact",
        state="publish",
        rtt_ms=rtt_ms,
        packets_retransmitted=0,
        packets_lost=0,
        status=status,
        message=message,
        send_rate_mbps=3.5,
        link_capacity_mbps=100.0,
        link_utilization_percent=3.5,
    )

    path = SRTPathHealth(
        name="impact",
        connections=(connection,),
        average_rtt_ms=rtt_ms,
        total_packets_retransmitted=0,
        total_packets_lost=0,
        status=status,
        message=message,
        maximum_rtt_ms=rtt_ms,
        average_link_utilization_percent=3.5,
    )

    return StreamingHealth(
        captured_at=captured_at,
        paths=(path,),
        status=status,
        message=message,
    )


def test_brief_degradation_keeps_effective_path_and_global_health() -> None:
    connection_stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    stabilizer = StreamingHealthStabilizer(
        connection_stabilizer=connection_stabilizer,
    )

    healthy = make_health(
        captured_at=BASE_TIME,
        status=HealthStatus.HEALTHY,
        rtt_ms=5.0,
        message="Streaming healthy.",
    )

    degraded = make_health(
        captured_at=BASE_TIME + timedelta(seconds=1),
        status=HealthStatus.DEGRADED,
        rtt_ms=120.0,
        message="Streaming degraded.",
    )

    first = stabilizer.stabilize(healthy)
    result = stabilizer.stabilize(degraded)

    assert first is healthy

    assert result.captured_at == degraded.captured_at

    assert result.status is HealthStatus.HEALTHY
    assert result.paths[0].status is HealthStatus.HEALTHY
    assert result.paths[0].connections[0].status is HealthStatus.HEALTHY

    # Current technical evidence must not be replaced by old evidence.
    assert result.paths[0].connections[0].rtt_ms == 120.0
    assert result.paths[0].average_rtt_ms == 120.0
    assert result.paths[0].maximum_rtt_ms == 120.0


def test_persistent_degradation_updates_connection_path_and_global_health() -> None:
    connection_stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    stabilizer = StreamingHealthStabilizer(
        connection_stabilizer=connection_stabilizer,
    )

    healthy = make_health(
        captured_at=BASE_TIME,
        status=HealthStatus.HEALTHY,
        rtt_ms=5.0,
        message="Streaming healthy.",
    )

    degraded_1 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=1),
        status=HealthStatus.DEGRADED,
        rtt_ms=120.0,
        message="Streaming degraded.",
    )

    degraded_2 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=11),
        status=HealthStatus.DEGRADED,
        rtt_ms=130.0,
        message="Streaming degraded.",
    )

    first = stabilizer.stabilize(healthy)
    held = stabilizer.stabilize(degraded_1)
    committed = stabilizer.stabilize(degraded_2)

    assert first.status is HealthStatus.HEALTHY

    assert held.status is HealthStatus.HEALTHY
    assert held.paths[0].status is HealthStatus.HEALTHY
    assert held.paths[0].connections[0].status is HealthStatus.HEALTHY

    assert committed.status is HealthStatus.DEGRADED
    assert committed.paths[0].status is HealthStatus.DEGRADED
    assert committed.paths[0].connections[0].status is HealthStatus.DEGRADED

    assert committed.captured_at == degraded_2.captured_at
    assert committed.paths[0].connections[0].rtt_ms == 130.0
    assert committed.paths[0].average_rtt_ms == 130.0
    assert committed.paths[0].maximum_rtt_ms == 130.0


def test_recovery_updates_connection_path_and_global_only_after_confirmation() -> None:
    connection_stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    stabilizer = StreamingHealthStabilizer(
        connection_stabilizer=connection_stabilizer,
    )

    degraded = make_health(
        captured_at=BASE_TIME,
        status=HealthStatus.DEGRADED,
        rtt_ms=120.0,
        message="Streaming degraded.",
    )

    healthy_1 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=1),
        status=HealthStatus.HEALTHY,
        rtt_ms=5.0,
        message="Streaming healthy.",
    )

    healthy_2 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=11),
        status=HealthStatus.HEALTHY,
        rtt_ms=4.0,
        message="Streaming healthy.",
    )

    first = stabilizer.stabilize(degraded)
    held = stabilizer.stabilize(healthy_1)
    recovered = stabilizer.stabilize(healthy_2)

    assert first.status is HealthStatus.DEGRADED

    assert held.status is HealthStatus.DEGRADED
    assert held.paths[0].status is HealthStatus.DEGRADED
    assert held.paths[0].connections[0].status is HealthStatus.DEGRADED

    assert recovered.status is HealthStatus.HEALTHY
    assert recovered.paths[0].status is HealthStatus.HEALTHY
    assert recovered.paths[0].connections[0].status is HealthStatus.HEALTHY

    assert recovered.captured_at == healthy_2.captured_at
    assert recovered.paths[0].connections[0].rtt_ms == 4.0
    assert recovered.paths[0].average_rtt_ms == 4.0
    assert recovered.paths[0].maximum_rtt_ms == 4.0


def test_persistent_critical_updates_path_and_global_health() -> None:
    connection_stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    stabilizer = StreamingHealthStabilizer(
        connection_stabilizer=connection_stabilizer,
    )

    healthy = make_health(
        captured_at=BASE_TIME,
        status=HealthStatus.HEALTHY,
        rtt_ms=5.0,
        message="Streaming healthy.",
    )

    critical_1 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=1),
        status=HealthStatus.CRITICAL,
        rtt_ms=300.0,
        message="Streaming critical.",
    )

    critical_2 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=11),
        status=HealthStatus.CRITICAL,
        rtt_ms=310.0,
        message="Streaming critical.",
    )

    stabilizer.stabilize(healthy)
    held = stabilizer.stabilize(critical_1)
    committed = stabilizer.stabilize(critical_2)

    assert held.status is HealthStatus.HEALTHY
    assert held.paths[0].status is HealthStatus.HEALTHY
    assert (
        held.paths[0].connections[0].status
        is HealthStatus.HEALTHY
    )

    assert committed.status is HealthStatus.CRITICAL
    assert committed.paths[0].status is HealthStatus.CRITICAL
    assert (
        committed.paths[0].connections[0].status
        is HealthStatus.CRITICAL
    )

    assert committed.captured_at == critical_2.captured_at
    assert committed.paths[0].connections[0].rtt_ms == 310.0


def test_persistent_unknown_updates_path_and_global_health() -> None:
    connection_stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    stabilizer = StreamingHealthStabilizer(
        connection_stabilizer=connection_stabilizer,
    )

    healthy = make_health(
        captured_at=BASE_TIME,
        status=HealthStatus.HEALTHY,
        rtt_ms=5.0,
        message="Streaming healthy.",
    )

    unknown_1 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=1),
        status=HealthStatus.UNKNOWN,
        rtt_ms=0.0,
        message="Streaming health unknown.",
    )

    unknown_2 = make_health(
        captured_at=BASE_TIME + timedelta(seconds=11),
        status=HealthStatus.UNKNOWN,
        rtt_ms=0.0,
        message="Streaming health unknown.",
    )

    stabilizer.stabilize(healthy)
    held = stabilizer.stabilize(unknown_1)
    committed = stabilizer.stabilize(unknown_2)

    assert held.status is HealthStatus.HEALTHY
    assert held.paths[0].status is HealthStatus.HEALTHY
    assert (
        held.paths[0].connections[0].status
        is HealthStatus.HEALTHY
    )

    assert committed.status is HealthStatus.UNKNOWN
    assert committed.paths[0].status is HealthStatus.UNKNOWN
    assert (
        committed.paths[0].connections[0].status
        is HealthStatus.UNKNOWN
    )

    assert committed.captured_at == unknown_2.captured_at


def test_multiple_paths_use_worst_stabilized_health() -> None:
    connection_stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=0.0,
        recovery_seconds=0.0,
    )

    stabilizer = StreamingHealthStabilizer(
        connection_stabilizer=connection_stabilizer,
    )

    healthy_connection = SRTConnectionHealth(
        connection_id="conn-healthy",
        path_name="enlace",
        state="publish",
        rtt_ms=5.0,
        packets_retransmitted=0,
        packets_lost=0,
        status=HealthStatus.HEALTHY,
        message="Healthy.",
    )

    degraded_connection = SRTConnectionHealth(
        connection_id="conn-degraded",
        path_name="impact",
        state="publish",
        rtt_ms=120.0,
        packets_retransmitted=0,
        packets_lost=0,
        status=HealthStatus.DEGRADED,
        message="Degraded.",
    )

    health = StreamingHealth(
        captured_at=BASE_TIME,
        paths=(
            SRTPathHealth(
                name="enlace",
                connections=(healthy_connection,),
                average_rtt_ms=5.0,
                total_packets_retransmitted=0,
                total_packets_lost=0,
                status=HealthStatus.HEALTHY,
                message="Healthy.",
                maximum_rtt_ms=5.0,
            ),
            SRTPathHealth(
                name="impact",
                connections=(degraded_connection,),
                average_rtt_ms=120.0,
                total_packets_retransmitted=0,
                total_packets_lost=0,
                status=HealthStatus.DEGRADED,
                message="Degraded.",
                maximum_rtt_ms=120.0,
            ),
        ),
        status=HealthStatus.DEGRADED,
        message="Streaming degraded.",
    )

    result = stabilizer.stabilize(health)

    assert result.paths[0].status is HealthStatus.HEALTHY
    assert result.paths[1].status is HealthStatus.DEGRADED
    assert result.status is HealthStatus.DEGRADED
