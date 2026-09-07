"""Tests for temporal SRT connection-health stabilization.

ENG-013B — Stream Health Block 2
"""

from datetime import UTC, datetime, timedelta

from app.domain.streaming.health import (
    HealthStatus,
    SRTConnectionHealth,
)
from app.services.srt_connection_health_stabilizer import (
    SRTConnectionHealthStabilizer,
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
    status: HealthStatus,
    *,
    message: str,
) -> SRTConnectionHealth:
    return SRTConnectionHealth(
        connection_id="conn-1",
        path_name="impact",
        state="publish",
        rtt_ms=5.0,
        packets_retransmitted=0,
        packets_lost=0,
        status=status,
        message=message,
        send_rate_mbps=3.5,
        link_capacity_mbps=100.0,
        link_utilization_percent=3.5,
    )


def test_brief_srt_degradation_does_not_replace_healthy_state() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    degraded = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection degraded.",
    )

    first = stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert first is healthy

    # Instantaneous evidence says DEGRADED, but the effective
    # temporally stabilized state must remain HEALTHY until
    # the degradation confirmation interval is satisfied.
    assert degraded.status is HealthStatus.DEGRADED
    assert result.status is HealthStatus.HEALTHY

    # Temporal stabilization must preserve the current
    # observation evidence rather than reverting to stale data.
    assert result.connection_id == degraded.connection_id
    assert result.path_name == degraded.path_name
    assert result.rtt_ms == degraded.rtt_ms
    assert result.packets_retransmitted == degraded.packets_retransmitted
    assert result.packets_lost == degraded.packets_lost


def test_persistent_srt_degradation_commits_after_confirmation() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    degraded_1 = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection degraded.",
    )

    degraded_10 = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection still degraded.",
    )

    degraded_11 = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection persistently degraded.",
    )

    assert (
        stabilizer.stabilize(
            healthy,
            observed_at=BASE_TIME,
        )
        is healthy
    )

    result_1 = stabilizer.stabilize(
        degraded_1,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result_1.status is HealthStatus.HEALTHY

    result_10 = stabilizer.stabilize(
        degraded_10,
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    assert result_10.status is HealthStatus.HEALTHY

    result_11 = stabilizer.stabilize(
        degraded_11,
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result_11 is degraded_11
    assert result_11.status is HealthStatus.DEGRADED


def test_srt_recovery_requires_recovery_confirmation() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=3.0,
        recovery_seconds=5.0,
    )

    degraded = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection degraded.",
    )

    healthy_1 = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection appears healthy.",
    )

    healthy_4 = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection still appears healthy.",
    )

    healthy_6 = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection stably healthy.",
    )

    assert (
        stabilizer.stabilize(
            degraded,
            observed_at=BASE_TIME,
        )
        is degraded
    )

    result_1 = stabilizer.stabilize(
        healthy_1,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result_1.status is HealthStatus.DEGRADED

    result_4 = stabilizer.stabilize(
        healthy_4,
        observed_at=BASE_TIME + timedelta(seconds=4),
    )

    assert result_4.status is HealthStatus.DEGRADED

    result_6 = stabilizer.stabilize(
        healthy_6,
        observed_at=BASE_TIME + timedelta(seconds=6),
    )

    assert result_6 is healthy_6
    assert result_6.status is HealthStatus.HEALTHY


def test_srt_degradation_candidate_is_cancelled_when_healthy_returns() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy_0 = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    degraded_1 = make_health(
        HealthStatus.DEGRADED,
        message="Temporary SRT degradation.",
    )

    healthy_2 = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy again.",
    )

    degraded_3 = make_health(
        HealthStatus.DEGRADED,
        message="New SRT degradation.",
    )

    degraded_11 = make_health(
        HealthStatus.DEGRADED,
        message="Second degradation still present.",
    )

    stabilizer.stabilize(
        healthy_0,
        observed_at=BASE_TIME,
    )

    result_1 = stabilizer.stabilize(
        degraded_1,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result_1.status is HealthStatus.HEALTHY

    assert (
        stabilizer.stabilize(
            healthy_2,
            observed_at=BASE_TIME + timedelta(seconds=2),
        )
        is healthy_2
    )

    result_3 = stabilizer.stabilize(
        degraded_3,
        observed_at=BASE_TIME + timedelta(seconds=3),
    )

    assert result_3.status is HealthStatus.HEALTHY

    result_11 = stabilizer.stabilize(
        degraded_11,
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    # The first degradation interval must not be accumulated.
    # This second candidate started at t=3, so only 8 seconds
    # have elapsed toward the 10-second confirmation interval.
    assert result_11.status is HealthStatus.HEALTHY


def test_srt_connections_are_stabilized_independently() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    connection_1_healthy = make_health(
        HealthStatus.HEALTHY,
        message="Connection 1 healthy.",
    )

    connection_1_degraded = make_health(
        HealthStatus.DEGRADED,
        message="Connection 1 degraded.",
    )

    connection_2_degraded = SRTConnectionHealth(
        connection_id="conn-2",
        path_name="enlace",
        state="publish",
        rtt_ms=120.0,
        packets_retransmitted=10,
        packets_lost=5,
        status=HealthStatus.DEGRADED,
        message="Connection 2 degraded.",
        send_rate_mbps=3.5,
        link_capacity_mbps=100.0,
        link_utilization_percent=3.5,
    )

    stabilizer.stabilize(
        connection_1_healthy,
        observed_at=BASE_TIME,
    )

    result_1 = stabilizer.stabilize(
        connection_1_degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    result_2 = stabilizer.stabilize(
        connection_2_degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    # Connection 1 already had HEALTHY as its committed state,
    # so its DEGRADED observation remains only a candidate.
    assert result_1.status is HealthStatus.HEALTHY

    # Connection 2 has never been observed before. Its first
    # observation establishes its own independent baseline.
    assert result_2 is connection_2_degraded
    assert result_2.status is HealthStatus.DEGRADED


def test_srt_health_rejects_observations_that_move_backwards_in_time() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    degraded = make_health(
        HealthStatus.DEGRADED,
        message="Out-of-order degradation observation.",
    )

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    try:
        stabilizer.stabilize(
            degraded,
            observed_at=BASE_TIME + timedelta(seconds=9),
        )
    except ValueError as exc:
        assert "backwards in time" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for backwards SRT health observation"
        )


def test_srt_health_rejects_negative_degradation_delay() -> None:
    try:
        SRTConnectionHealthStabilizer(
            degradation_seconds=-1.0,
            recovery_seconds=5.0,
        )
    except ValueError as exc:
        assert "degradation_seconds" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for negative degradation_seconds"
        )


def test_srt_health_rejects_negative_recovery_delay() -> None:
    try:
        SRTConnectionHealthStabilizer(
            degradation_seconds=3.0,
            recovery_seconds=-1.0,
        )
    except ValueError as exc:
        assert "recovery_seconds" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for negative recovery_seconds"
        )


def test_brief_srt_critical_observation_does_not_replace_healthy_state() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    critical = make_health(
        HealthStatus.CRITICAL,
        message="Temporary critical SRT observation.",
    )

    assert (
        stabilizer.stabilize(
            healthy,
            observed_at=BASE_TIME,
        )
        is healthy
    )

    result = stabilizer.stabilize(
        critical,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert critical.status is HealthStatus.CRITICAL
    assert result.status is HealthStatus.HEALTHY


def test_persistent_srt_critical_commits_after_confirmation() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    critical_1 = make_health(
        HealthStatus.CRITICAL,
        message="Critical SRT observation.",
    )

    critical_10 = make_health(
        HealthStatus.CRITICAL,
        message="Critical SRT observation still present.",
    )

    critical_11 = make_health(
        HealthStatus.CRITICAL,
        message="Critical SRT condition persistently present.",
    )

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    result_1 = stabilizer.stabilize(
        critical_1,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result_1.status is HealthStatus.HEALTHY

    result_10 = stabilizer.stabilize(
        critical_10,
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    assert result_10.status is HealthStatus.HEALTHY

    result_11 = stabilizer.stabilize(
        critical_11,
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result_11 is critical_11
    assert result_11.status is HealthStatus.CRITICAL


def test_brief_srt_unknown_does_not_replace_known_stable_state() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    unknown = make_health(
        HealthStatus.UNKNOWN,
        message="Insufficient SRT telemetry.",
    )

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        unknown,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert unknown.status is HealthStatus.UNKNOWN
    assert result.status is HealthStatus.HEALTHY


def test_persistent_srt_unknown_commits_after_confirmation() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    unknown_1 = make_health(
        HealthStatus.UNKNOWN,
        message="SRT telemetry unavailable.",
    )

    unknown_10 = make_health(
        HealthStatus.UNKNOWN,
        message="SRT telemetry still unavailable.",
    )

    unknown_11 = make_health(
        HealthStatus.UNKNOWN,
        message="SRT telemetry persistently unavailable.",
    )

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    result_1 = stabilizer.stabilize(
        unknown_1,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result_1.status is HealthStatus.HEALTHY

    result_10 = stabilizer.stabilize(
        unknown_10,
        observed_at=BASE_TIME + timedelta(seconds=10),
    )

    assert result_10.status is HealthStatus.HEALTHY

    result_11 = stabilizer.stabilize(
        unknown_11,
        observed_at=BASE_TIME + timedelta(seconds=11),
    )

    assert result_11 is unknown_11
    assert result_11.status is HealthStatus.UNKNOWN


def test_zero_degradation_delay_commits_first_candidate_immediately() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=0.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    degraded = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection degraded.",
    )

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result is degraded
    assert result.status is HealthStatus.DEGRADED


def test_zero_recovery_delay_commits_first_healthy_candidate_immediately() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=0.0,
    )

    degraded = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection degraded.",
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy again.",
    )

    stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME,
    )

    result = stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result is healthy
    assert result.status is HealthStatus.HEALTHY


def test_srt_health_reset_removes_connection_temporal_state() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    healthy = make_health(
        HealthStatus.HEALTHY,
        message="SRT connection healthy.",
    )

    degraded = make_health(
        HealthStatus.DEGRADED,
        message="SRT connection degraded.",
    )

    stabilizer.stabilize(
        healthy,
        observed_at=BASE_TIME,
    )

    held = stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert held.status is HealthStatus.HEALTHY

    stabilizer.reset("conn-1")

    result = stabilizer.stabilize(
        degraded,
        observed_at=BASE_TIME + timedelta(seconds=2),
    )

    # After reset this is a first observation again,
    # so it establishes a fresh baseline immediately.
    assert result is degraded
    assert result.status is HealthStatus.DEGRADED


def test_srt_health_reset_without_connection_id_clears_all_state() -> None:
    stabilizer = SRTConnectionHealthStabilizer(
        degradation_seconds=10.0,
        recovery_seconds=10.0,
    )

    connection_1_healthy = make_health(
        HealthStatus.HEALTHY,
        message="Connection 1 healthy.",
    )

    connection_2_healthy = SRTConnectionHealth(
        connection_id="conn-2",
        path_name="enlace",
        state="publish",
        rtt_ms=5.0,
        packets_retransmitted=0,
        packets_lost=0,
        status=HealthStatus.HEALTHY,
        message="Connection 2 healthy.",
        send_rate_mbps=3.5,
        link_capacity_mbps=100.0,
        link_utilization_percent=3.5,
    )

    connection_1_degraded = make_health(
        HealthStatus.DEGRADED,
        message="Connection 1 degraded.",
    )

    connection_2_degraded = SRTConnectionHealth(
        connection_id="conn-2",
        path_name="enlace",
        state="publish",
        rtt_ms=120.0,
        packets_retransmitted=10,
        packets_lost=5,
        status=HealthStatus.DEGRADED,
        message="Connection 2 degraded.",
        send_rate_mbps=3.5,
        link_capacity_mbps=100.0,
        link_utilization_percent=3.5,
    )

    stabilizer.stabilize(
        connection_1_healthy,
        observed_at=BASE_TIME,
    )

    stabilizer.stabilize(
        connection_2_healthy,
        observed_at=BASE_TIME,
    )

    stabilizer.reset()

    result_1 = stabilizer.stabilize(
        connection_1_degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    result_2 = stabilizer.stabilize(
        connection_2_degraded,
        observed_at=BASE_TIME + timedelta(seconds=1),
    )

    assert result_1 is connection_1_degraded
    assert result_1.status is HealthStatus.DEGRADED

    assert result_2 is connection_2_degraded
    assert result_2.status is HealthStatus.DEGRADED
