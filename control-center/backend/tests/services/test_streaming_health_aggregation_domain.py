import pytest

from app.domain.streaming.aggregation import HealthPopulation


def test_health_population_exposes_derived_counts() -> None:
    population = HealthPopulation(
        healthy_count=4,
        degraded_count=2,
        critical_count=1,
        unknown_count=3,
    )

    assert population.known_count == 7
    assert population.total_count == 10
    assert population.affected_count == 3


def test_health_population_exposes_derived_fractions() -> None:
    population = HealthPopulation(
        healthy_count=4,
        degraded_count=2,
        critical_count=1,
        unknown_count=3,
    )

    assert population.affected_fraction == pytest.approx(3 / 7)
    assert population.evidence_coverage == pytest.approx(7 / 10)


def test_health_population_uses_none_when_fraction_denominator_is_zero() -> None:
    population = HealthPopulation(
        healthy_count=0,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )

    assert population.known_count == 0
    assert population.total_count == 0
    assert population.affected_count == 0
    assert population.affected_fraction is None
    assert population.evidence_coverage is None


@pytest.mark.parametrize(
    (
        "healthy_count",
        "degraded_count",
        "critical_count",
        "unknown_count",
    ),
    [
        (-1, 0, 0, 0),
        (0, -1, 0, 0),
        (0, 0, -1, 0),
        (0, 0, 0, -1),
    ],
)
def test_health_population_rejects_negative_counts(
    healthy_count: int,
    degraded_count: int,
    critical_count: int,
    unknown_count: int,
) -> None:
    with pytest.raises(ValueError):
        HealthPopulation(
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            critical_count=critical_count,
            unknown_count=unknown_count,
        )

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.aggregation import (
    resolve_aggregate_status,
    resolve_worst_status,
)


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((HealthStatus.HEALTHY,), HealthStatus.HEALTHY),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
            ),
            HealthStatus.DEGRADED,
        ),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.HEALTHY,
                HealthStatus.CRITICAL,
            ),
            HealthStatus.DEGRADED,
        ),
        (
            (
                HealthStatus.DEGRADED,
                HealthStatus.DEGRADED,
                HealthStatus.CRITICAL,
            ),
            HealthStatus.CRITICAL,
        ),
        (
            (
                HealthStatus.CRITICAL,
                HealthStatus.CRITICAL,
            ),
            HealthStatus.CRITICAL,
        ),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.UNKNOWN,
                HealthStatus.UNKNOWN,
            ),
            HealthStatus.HEALTHY,
        ),
        (
            (
                HealthStatus.CRITICAL,
                HealthStatus.UNKNOWN,
                HealthStatus.UNKNOWN,
            ),
            HealthStatus.CRITICAL,
        ),
        (
            (
                HealthStatus.UNKNOWN,
                HealthStatus.UNKNOWN,
            ),
            HealthStatus.UNKNOWN,
        ),
        ((), HealthStatus.UNKNOWN),
    ],
)
def test_resolve_aggregate_status(
    statuses: tuple[HealthStatus, ...],
    expected: HealthStatus,
) -> None:
    assert resolve_aggregate_status(statuses) is expected


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((HealthStatus.HEALTHY,), HealthStatus.HEALTHY),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
            ),
            HealthStatus.DEGRADED,
        ),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.CRITICAL,
            ),
            HealthStatus.CRITICAL,
        ),
        (
            (
                HealthStatus.DEGRADED,
                HealthStatus.CRITICAL,
            ),
            HealthStatus.CRITICAL,
        ),
        (
            (
                HealthStatus.HEALTHY,
                HealthStatus.UNKNOWN,
            ),
            HealthStatus.HEALTHY,
        ),
        (
            (
                HealthStatus.UNKNOWN,
                HealthStatus.UNKNOWN,
            ),
            HealthStatus.UNKNOWN,
        ),
        ((), HealthStatus.UNKNOWN),
    ],
)
def test_resolve_worst_status(
    statuses: tuple[HealthStatus, ...],
    expected: HealthStatus,
) -> None:
    assert resolve_worst_status(statuses) is expected


from app.domain.sessions import SessionProtocol
from app.domain.streaming.aggregation import ProtocolHealth


def test_protocol_health_accepts_consistent_population_and_roles() -> None:
    health = ProtocolHealth(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        population=HealthPopulation(
            healthy_count=2,
            degraded_count=1,
            critical_count=0,
            unknown_count=1,
        ),
        reader_count=2,
        publisher_count=1,
        unknown_role_count=1,
        status=HealthStatus.DEGRADED,
        worst_observed_status=HealthStatus.DEGRADED,
        message="SRT health for IMPACT.",
    )

    assert health.service_id == "IMPACT"
    assert health.protocol is SessionProtocol.SRT
    assert health.population.total_count == 4
    assert health.reader_count == 2
    assert health.publisher_count == 1
    assert health.unknown_role_count == 1
    assert health.status is HealthStatus.DEGRADED
    assert health.worst_observed_status is HealthStatus.DEGRADED


@pytest.mark.parametrize(
    (
        "reader_count",
        "publisher_count",
        "unknown_role_count",
    ),
    [
        (-1, 2, 1),
        (2, -1, 1),
        (2, 1, -1),
    ],
)
def test_protocol_health_rejects_negative_role_counts(
    reader_count: int,
    publisher_count: int,
    unknown_role_count: int,
) -> None:
    with pytest.raises(ValueError):
        ProtocolHealth(
            service_id="IMPACT",
            protocol=SessionProtocol.SRT,
            population=HealthPopulation(
                healthy_count=2,
                degraded_count=1,
                critical_count=0,
                unknown_count=1,
            ),
            reader_count=reader_count,
            publisher_count=publisher_count,
            unknown_role_count=unknown_role_count,
            status=HealthStatus.DEGRADED,
            worst_observed_status=HealthStatus.DEGRADED,
            message="SRT health for IMPACT.",
        )


def test_protocol_health_rejects_role_population_mismatch() -> None:
    with pytest.raises(ValueError):
        ProtocolHealth(
            service_id="IMPACT",
            protocol=SessionProtocol.SRT,
            population=HealthPopulation(
                healthy_count=2,
                degraded_count=1,
                critical_count=0,
                unknown_count=1,
            ),
            reader_count=1,
            publisher_count=1,
            unknown_role_count=1,
            status=HealthStatus.DEGRADED,
            worst_observed_status=HealthStatus.DEGRADED,
            message="SRT health for IMPACT.",
        )


@pytest.mark.parametrize(
    "service_id",
    [
        "",
        "   ",
    ],
)
def test_protocol_health_rejects_blank_service_id(
    service_id: str,
) -> None:
    with pytest.raises(ValueError):
        ProtocolHealth(
            service_id=service_id,
            protocol=SessionProtocol.SRT,
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            reader_count=1,
            publisher_count=0,
            unknown_role_count=0,
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message="SRT health.",
        )


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
def test_protocol_health_rejects_blank_message(
    message: str,
) -> None:
    with pytest.raises(ValueError):
        ProtocolHealth(
            service_id="IMPACT",
            protocol=SessionProtocol.SRT,
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            reader_count=1,
            publisher_count=0,
            unknown_role_count=0,
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message=message,
        )


from app.domain.streaming.aggregation import ServiceHealth


def _protocol_health(
    *,
    service_id: str,
    protocol: SessionProtocol,
    healthy: int = 0,
    degraded: int = 0,
    critical: int = 0,
    unknown: int = 0,
) -> ProtocolHealth:
    population = HealthPopulation(
        healthy_count=healthy,
        degraded_count=degraded,
        critical_count=critical,
        unknown_count=unknown,
    )

    return ProtocolHealth(
        service_id=service_id,
        protocol=protocol,
        population=population,
        reader_count=population.total_count,
        publisher_count=0,
        unknown_role_count=0,
        status=resolve_aggregate_status(
            (
                *((HealthStatus.HEALTHY,) * healthy),
                *((HealthStatus.DEGRADED,) * degraded),
                *((HealthStatus.CRITICAL,) * critical),
                *((HealthStatus.UNKNOWN,) * unknown),
            )
        ),
        worst_observed_status=resolve_worst_status(
            (
                *((HealthStatus.HEALTHY,) * healthy),
                *((HealthStatus.DEGRADED,) * degraded),
                *((HealthStatus.CRITICAL,) * critical),
                *((HealthStatus.UNKNOWN,) * unknown),
            )
        ),
        message=f"{protocol.value} health for {service_id}.",
    )


def test_service_health_accepts_consistent_protocols_and_population() -> None:
    srt = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=2,
        degraded=1,
    )
    hls = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.HLS,
        healthy=1,
        unknown=1,
    )

    health = ServiceHealth(
        service_id="IMPACT",
        protocols=(srt, hls),
        population=HealthPopulation(
            healthy_count=3,
            degraded_count=1,
            critical_count=0,
            unknown_count=1,
        ),
        status=HealthStatus.DEGRADED,
        worst_observed_status=HealthStatus.DEGRADED,
        message="Service IMPACT health.",
    )

    assert health.service_id == "IMPACT"
    assert health.protocols == (srt, hls)
    assert health.population.total_count == 5
    assert health.status is HealthStatus.DEGRADED
    assert health.worst_observed_status is HealthStatus.DEGRADED


@pytest.mark.parametrize(
    "service_id",
    [
        "",
        "   ",
    ],
)
def test_service_health_rejects_blank_service_id(
    service_id: str,
) -> None:
    protocol = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=1,
    )

    with pytest.raises(ValueError):
        ServiceHealth(
            service_id=service_id,
            protocols=(protocol,),
            population=protocol.population,
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message="Service health.",
        )


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
def test_service_health_rejects_blank_message(
    message: str,
) -> None:
    protocol = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=1,
    )

    with pytest.raises(ValueError):
        ServiceHealth(
            service_id="IMPACT",
            protocols=(protocol,),
            population=protocol.population,
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message=message,
        )


def test_service_health_rejects_protocol_from_different_service() -> None:
    protocol = _protocol_health(
        service_id="ENLACE",
        protocol=SessionProtocol.SRT,
        healthy=1,
    )

    with pytest.raises(ValueError):
        ServiceHealth(
            service_id="IMPACT",
            protocols=(protocol,),
            population=protocol.population,
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message="Service IMPACT health.",
        )


def test_service_health_rejects_duplicate_protocols() -> None:
    first = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=1,
    )
    second = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        degraded=1,
    )

    with pytest.raises(ValueError):
        ServiceHealth(
            service_id="IMPACT",
            protocols=(first, second),
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=1,
                critical_count=0,
                unknown_count=0,
            ),
            status=HealthStatus.DEGRADED,
            worst_observed_status=HealthStatus.DEGRADED,
            message="Service IMPACT health.",
        )


def test_service_health_rejects_population_mismatch() -> None:
    protocol = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=2,
    )

    with pytest.raises(ValueError):
        ServiceHealth(
            service_id="IMPACT",
            protocols=(protocol,),
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message="Service IMPACT health.",
        )


from datetime import datetime, timezone

from app.domain.streaming.aggregation import PlatformHealth


def _service_health(
    *,
    service_id: str,
    protocols: tuple[ProtocolHealth, ...],
    status: HealthStatus,
    worst: HealthStatus,
) -> ServiceHealth:
    population = HealthPopulation(
        healthy_count=sum(
            protocol.population.healthy_count
            for protocol in protocols
        ),
        degraded_count=sum(
            protocol.population.degraded_count
            for protocol in protocols
        ),
        critical_count=sum(
            protocol.population.critical_count
            for protocol in protocols
        ),
        unknown_count=sum(
            protocol.population.unknown_count
            for protocol in protocols
        ),
    )

    return ServiceHealth(
        service_id=service_id,
        protocols=protocols,
        population=population,
        status=status,
        worst_observed_status=worst,
        message=f"Service {service_id} health.",
    )


def test_platform_health_accepts_consistent_services_and_population() -> None:
    impact_protocol = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=2,
        degraded=1,
    )
    enlace_protocol = _protocol_health(
        service_id="ENLACE",
        protocol=SessionProtocol.HLS,
        healthy=2,
    )

    impact = _service_health(
        service_id="IMPACT",
        protocols=(impact_protocol,),
        status=HealthStatus.DEGRADED,
        worst=HealthStatus.DEGRADED,
    )
    enlace = _service_health(
        service_id="ENLACE",
        protocols=(enlace_protocol,),
        status=HealthStatus.HEALTHY,
        worst=HealthStatus.HEALTHY,
    )

    captured_at = datetime(
        2026,
        9,
        9,
        13,
        30,
        tzinfo=timezone.utc,
    )

    health = PlatformHealth(
        captured_at=captured_at,
        services=(enlace, impact),
        population=HealthPopulation(
            healthy_count=4,
            degraded_count=1,
            critical_count=0,
            unknown_count=0,
        ),
        status=HealthStatus.DEGRADED,
        worst_observed_status=HealthStatus.DEGRADED,
        message="Platform health.",
    )

    assert health.captured_at == captured_at
    assert health.services == (enlace, impact)
    assert health.population.total_count == 5
    assert health.status is HealthStatus.DEGRADED
    assert health.worst_observed_status is HealthStatus.DEGRADED


def test_platform_health_accepts_empty_platform() -> None:
    health = PlatformHealth(
        captured_at=datetime(
            2026,
            9,
            9,
            13,
            30,
            tzinfo=timezone.utc,
        ),
        services=(),
        population=HealthPopulation(
            healthy_count=0,
            degraded_count=0,
            critical_count=0,
            unknown_count=0,
        ),
        status=HealthStatus.UNKNOWN,
        worst_observed_status=HealthStatus.UNKNOWN,
        message="No active multimedia sessions were observed.",
    )

    assert health.services == ()
    assert health.population.total_count == 0
    assert health.status is HealthStatus.UNKNOWN


def test_platform_health_rejects_naive_captured_at() -> None:
    with pytest.raises(ValueError):
        PlatformHealth(
            captured_at=datetime(2026, 9, 9, 13, 30),
            services=(),
            population=HealthPopulation(
                healthy_count=0,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            status=HealthStatus.UNKNOWN,
            worst_observed_status=HealthStatus.UNKNOWN,
            message="Platform health.",
        )


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
def test_platform_health_rejects_blank_message(
    message: str,
) -> None:
    with pytest.raises(ValueError):
        PlatformHealth(
            captured_at=datetime(
                2026,
                9,
                9,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            services=(),
            population=HealthPopulation(
                healthy_count=0,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            status=HealthStatus.UNKNOWN,
            worst_observed_status=HealthStatus.UNKNOWN,
            message=message,
        )


def test_platform_health_rejects_duplicate_service_ids() -> None:
    protocol = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=1,
    )

    first = _service_health(
        service_id="IMPACT",
        protocols=(protocol,),
        status=HealthStatus.HEALTHY,
        worst=HealthStatus.HEALTHY,
    )
    second = _service_health(
        service_id="IMPACT",
        protocols=(protocol,),
        status=HealthStatus.HEALTHY,
        worst=HealthStatus.HEALTHY,
    )

    with pytest.raises(ValueError):
        PlatformHealth(
            captured_at=datetime(
                2026,
                9,
                9,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            services=(first, second),
            population=HealthPopulation(
                healthy_count=2,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message="Platform health.",
        )


def test_platform_health_rejects_population_mismatch() -> None:
    protocol = _protocol_health(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        healthy=2,
    )

    service = _service_health(
        service_id="IMPACT",
        protocols=(protocol,),
        status=HealthStatus.HEALTHY,
        worst=HealthStatus.HEALTHY,
    )

    with pytest.raises(ValueError):
        PlatformHealth(
            captured_at=datetime(
                2026,
                9,
                9,
                13,
                30,
                tzinfo=timezone.utc,
            ),
            services=(service,),
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message="Platform health.",
        )


from datetime import UTC

from app.domain.sessions import SessionSnapshot
from app.domain.streaming.aggregation import StreamingHealthAggregator


def test_streaming_health_aggregator_builds_unknown_empty_platform() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        13,
        45,
        tzinfo=UTC,
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=(),
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=None,
    )

    assert health.captured_at == captured_at
    assert health.services == ()
    assert health.population == HealthPopulation(
        healthy_count=0,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )
    assert health.population.total_count == 0
    assert health.status is HealthStatus.UNKNOWN
    assert health.worst_observed_status is HealthStatus.UNKNOWN


from app.domain.sessions import (
    ActiveSession,
    SessionQuality,
    SessionRole,
)


def test_streaming_health_aggregator_maps_rtmp_good_session_to_healthy() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        14,
        0,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="rtmp-reader-1",
        protocol=SessionProtocol.RTMP,
        role=SessionRole.READER,
        state="read",
        remote_ip="203.0.113.10",
        remote_port=1935,
        path="IMPACT",
        connected_since=captured_at,
        quality=SessionQuality.GOOD,
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=(session,),
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=None,
    )

    assert health.captured_at == captured_at

    assert health.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )
    assert health.status is HealthStatus.HEALTHY
    assert health.worst_observed_status is HealthStatus.HEALTHY

    assert len(health.services) == 1

    service = health.services[0]

    assert service.service_id == "IMPACT"
    assert service.population == health.population
    assert service.status is HealthStatus.HEALTHY
    assert service.worst_observed_status is HealthStatus.HEALTHY

    assert len(service.protocols) == 1

    protocol = service.protocols[0]

    assert protocol.service_id == "IMPACT"
    assert protocol.protocol is SessionProtocol.RTMP
    assert protocol.population == health.population

    assert protocol.reader_count == 1
    assert protocol.publisher_count == 0
    assert protocol.unknown_role_count == 0

    assert protocol.status is HealthStatus.HEALTHY
    assert protocol.worst_observed_status is HealthStatus.HEALTHY


from app.domain.streaming.health import (
    SRTConnectionHealth,
    SRTPathHealth,
    StreamingHealth,
)


def test_streaming_health_aggregator_prefers_matching_srt_health() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        14,
        15,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="srt-reader-1",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="read",
        remote_ip="203.0.113.20",
        remote_port=8890,
        path="IMPACT",
        connected_since=captured_at,
        quality=SessionQuality.GOOD,
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=(session,),
    )

    specialized_connection = SRTConnectionHealth(
        connection_id="srt-reader-1",
        path_name="IMPACT",
        state="read",
        rtt_ms=300.0,
        packets_retransmitted=10,
        packets_lost=5,
        status=HealthStatus.CRITICAL,
        message="Critical SRT connection.",
    )

    specialized_path = SRTPathHealth(
        name="IMPACT",
        connections=(specialized_connection,),
        average_rtt_ms=300.0,
        total_packets_retransmitted=10,
        total_packets_lost=5,
        status=HealthStatus.CRITICAL,
        message="Critical SRT path.",
        maximum_rtt_ms=300.0,
    )

    streaming_health = StreamingHealth(
        captured_at=captured_at,
        paths=(specialized_path,),
        status=HealthStatus.CRITICAL,
        message="Critical streaming health.",
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=streaming_health,
    )

    assert health.population == HealthPopulation(
        healthy_count=0,
        degraded_count=0,
        critical_count=1,
        unknown_count=0,
    )

    assert health.status is HealthStatus.CRITICAL
    assert health.worst_observed_status is HealthStatus.CRITICAL

    assert len(health.services) == 1

    service = health.services[0]

    assert service.service_id == "IMPACT"
    assert service.status is HealthStatus.CRITICAL
    assert service.worst_observed_status is HealthStatus.CRITICAL

    assert len(service.protocols) == 1

    protocol = service.protocols[0]

    assert protocol.protocol is SessionProtocol.SRT
    assert protocol.population == health.population
    assert protocol.status is HealthStatus.CRITICAL
    assert protocol.worst_observed_status is HealthStatus.CRITICAL


def test_protocol_health_rejects_noncanonical_protocol() -> None:
    with pytest.raises(ValueError):
        ProtocolHealth(
            service_id="IMPACT",
            protocol="SRT",  # type: ignore[arg-type]
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            reader_count=1,
            publisher_count=0,
            unknown_role_count=0,
            status=HealthStatus.HEALTHY,
            worst_observed_status=HealthStatus.HEALTHY,
            message="SRT health for IMPACT.",
        )


@pytest.mark.parametrize(
    (
        "status",
        "worst_observed_status",
    ),
    [
        (
            "HEALTHY",
            HealthStatus.HEALTHY,
        ),
        (
            HealthStatus.HEALTHY,
            "HEALTHY",
        ),
    ],
)
def test_protocol_health_rejects_noncanonical_health_status(
    status: object,
    worst_observed_status: object,
) -> None:
    with pytest.raises(ValueError):
        ProtocolHealth(
            service_id="IMPACT",
            protocol=SessionProtocol.SRT,
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            reader_count=1,
            publisher_count=0,
            unknown_role_count=0,
            status=status,  # type: ignore[arg-type]
            worst_observed_status=worst_observed_status,  # type: ignore[arg-type]
            message="SRT health for IMPACT.",
        )


@pytest.mark.parametrize(
    (
        "status",
        "worst_observed_status",
    ),
    [
        (
            "HEALTHY",
            HealthStatus.HEALTHY,
        ),
        (
            HealthStatus.HEALTHY,
            "HEALTHY",
        ),
    ],
)
def test_service_health_rejects_noncanonical_health_status(
    status: object,
    worst_observed_status: object,
) -> None:
    protocol = ProtocolHealth(
        service_id="IMPACT",
        protocol=SessionProtocol.SRT,
        population=HealthPopulation(
            healthy_count=1,
            degraded_count=0,
            critical_count=0,
            unknown_count=0,
        ),
        reader_count=1,
        publisher_count=0,
        unknown_role_count=0,
        status=HealthStatus.HEALTHY,
        worst_observed_status=HealthStatus.HEALTHY,
        message="SRT health for IMPACT.",
    )

    with pytest.raises(ValueError):
        ServiceHealth(
            service_id="IMPACT",
            protocols=(protocol,),
            population=HealthPopulation(
                healthy_count=1,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            status=status,  # type: ignore[arg-type]
            worst_observed_status=worst_observed_status,  # type: ignore[arg-type]
            message="Service IMPACT health.",
        )


@pytest.mark.parametrize(
    (
        "status",
        "worst_observed_status",
    ),
    [
        (
            "HEALTHY",
            HealthStatus.HEALTHY,
        ),
        (
            HealthStatus.HEALTHY,
            "HEALTHY",
        ),
    ],
)
def test_platform_health_rejects_noncanonical_health_status(
    status: object,
    worst_observed_status: object,
) -> None:
    with pytest.raises(ValueError):
        PlatformHealth(
            captured_at=datetime(
                2026,
                9,
                9,
                14,
                30,
                tzinfo=UTC,
            ),
            services=(),
            population=HealthPopulation(
                healthy_count=0,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            ),
            status=status,  # type: ignore[arg-type]
            worst_observed_status=worst_observed_status,  # type: ignore[arg-type]
            message="Platform health.",
        )


def test_streaming_health_aggregator_preserves_hierarchical_status() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        15,
        0,
        tzinfo=UTC,
    )

    sessions = (
        ActiveSession(
            session_id="rtmp-impact-1",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.10",
            remote_port=5001,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.GOOD,
        ),
        ActiveSession(
            session_id="srt-impact-1",
            protocol=SessionProtocol.SRT,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.11",
            remote_port=5002,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.CRITICAL,
        ),
        ActiveSession(
            session_id="hls-enlace-1",
            protocol=SessionProtocol.HLS,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.12",
            remote_port=5003,
            path="ENLACE",
            connected_since=captured_at,
            quality=SessionQuality.GOOD,
        ),
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=sessions,
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=None,
    )

    assert health.population == HealthPopulation(
        healthy_count=2,
        degraded_count=0,
        critical_count=1,
        unknown_count=0,
    )

    assert health.status is HealthStatus.DEGRADED
    assert health.worst_observed_status is HealthStatus.CRITICAL

    assert tuple(
        service.service_id
        for service in health.services
    ) == (
        "ENLACE",
        "IMPACT",
    )

    enlace = health.services[0]
    impact = health.services[1]

    assert enlace.status is HealthStatus.HEALTHY
    assert enlace.worst_observed_status is HealthStatus.HEALTHY

    assert impact.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=1,
        unknown_count=0,
    )

    assert impact.status is HealthStatus.DEGRADED
    assert impact.worst_observed_status is HealthStatus.CRITICAL

    assert tuple(
        protocol.protocol
        for protocol in impact.protocols
    ) == (
        SessionProtocol.RTMP,
        SessionProtocol.SRT,
    )

    rtmp = impact.protocols[0]
    srt = impact.protocols[1]

    assert rtmp.status is HealthStatus.HEALTHY
    assert rtmp.worst_observed_status is HealthStatus.HEALTHY

    assert srt.status is HealthStatus.CRITICAL
    assert srt.worst_observed_status is HealthStatus.CRITICAL


def test_streaming_health_aggregator_preserves_unknown_population() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        15,
        30,
        tzinfo=UTC,
    )

    sessions = (
        ActiveSession(
            session_id="rtmp-impact-healthy",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.20",
            remote_port=5101,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.GOOD,
        ),
        ActiveSession(
            session_id="rtmp-impact-unknown-1",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.21",
            remote_port=5102,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.UNKNOWN,
        ),
        ActiveSession(
            session_id="rtmp-impact-unknown-2",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.22",
            remote_port=5103,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.UNKNOWN,
        ),
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=SessionSnapshot(
            captured_at=captured_at,
            sessions=sessions,
        ),
        streaming_health=None,
    )

    assert health.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=0,
        unknown_count=2,
    )

    assert health.population.known_count == 1
    assert health.population.total_count == 3
    assert health.population.affected_count == 0
    assert health.population.affected_fraction == 0.0
    assert health.population.evidence_coverage == pytest.approx(
        1 / 3
    )

    assert health.status is HealthStatus.HEALTHY
    assert health.worst_observed_status is HealthStatus.HEALTHY

    service = health.services[0]
    protocol = service.protocols[0]

    assert service.status is HealthStatus.HEALTHY
    assert protocol.status is HealthStatus.HEALTHY

    assert protocol.population.unknown_count == 2


def test_streaming_health_aggregator_returns_unknown_when_all_evidence_unknown() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        16,
        0,
        tzinfo=UTC,
    )

    sessions = (
        ActiveSession(
            session_id="rtmp-impact-unknown-1",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.30",
            remote_port=5201,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.UNKNOWN,
        ),
        ActiveSession(
            session_id="rtmp-impact-unknown-2",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.PUBLISHER,
            state="active",
            remote_ip="192.0.2.31",
            remote_port=5202,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.UNKNOWN,
        ),
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=SessionSnapshot(
            captured_at=captured_at,
            sessions=sessions,
        ),
        streaming_health=None,
    )

    assert health.population == HealthPopulation(
        healthy_count=0,
        degraded_count=0,
        critical_count=0,
        unknown_count=2,
    )

    assert health.population.known_count == 0
    assert health.population.total_count == 2
    assert health.population.affected_count == 0
    assert health.population.affected_fraction is None
    assert health.population.evidence_coverage == 0.0

    assert health.status is HealthStatus.UNKNOWN
    assert health.worst_observed_status is HealthStatus.UNKNOWN

    service = health.services[0]
    protocol = service.protocols[0]

    assert service.status is HealthStatus.UNKNOWN
    assert service.worst_observed_status is HealthStatus.UNKNOWN

    assert protocol.status is HealthStatus.UNKNOWN
    assert protocol.worst_observed_status is HealthStatus.UNKNOWN

    assert protocol.reader_count == 1
    assert protocol.publisher_count == 1
    assert protocol.unknown_role_count == 0


def test_streaming_health_aggregator_rejects_srt_path_mismatch() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        16,
        30,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="srt-reader-1",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="active",
        remote_ip="192.0.2.40",
        remote_port=5301,
        path="IMPACT",
        connected_since=captured_at,
        quality=SessionQuality.GOOD,
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=(session,),
    )

    specialized_connection = SRTConnectionHealth(
        connection_id="srt-reader-1",
        path_name="ENLACE",
        state="active",
        rtt_ms=300.0,
        packets_retransmitted=10,
        packets_lost=5,
        status=HealthStatus.CRITICAL,
        message="Critical SRT connection on another path.",
    )

    specialized_path = SRTPathHealth(
        name="ENLACE",
        connections=(specialized_connection,),
        average_rtt_ms=300.0,
        total_packets_retransmitted=10,
        total_packets_lost=5,
        status=HealthStatus.CRITICAL,
        message="Critical ENLACE path.",
        maximum_rtt_ms=300.0,
    )

    streaming_health = StreamingHealth(
        captured_at=captured_at,
        paths=(specialized_path,),
        status=HealthStatus.CRITICAL,
        message="Critical streaming health.",
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=streaming_health,
    )

    assert health.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )

    assert health.status is HealthStatus.HEALTHY
    assert health.worst_observed_status is HealthStatus.HEALTHY

    service = health.services[0]
    protocol = service.protocols[0]

    assert service.service_id == "IMPACT"
    assert protocol.protocol is SessionProtocol.SRT

    assert protocol.status is HealthStatus.HEALTHY
    assert protocol.worst_observed_status is HealthStatus.HEALTHY


def test_streaming_health_aggregator_ignores_orphan_srt_evidence() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        17,
        0,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="rtmp-impact-1",
        protocol=SessionProtocol.RTMP,
        role=SessionRole.READER,
        state="active",
        remote_ip="192.0.2.50",
        remote_port=5401,
        path="IMPACT",
        connected_since=captured_at,
        quality=SessionQuality.GOOD,
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=(session,),
    )

    orphan_connection = SRTConnectionHealth(
        connection_id="orphan-srt-1",
        path_name="ENLACE",
        state="active",
        rtt_ms=400.0,
        packets_retransmitted=20,
        packets_lost=10,
        status=HealthStatus.CRITICAL,
        message="Critical orphan SRT connection.",
    )

    orphan_path = SRTPathHealth(
        name="ENLACE",
        connections=(orphan_connection,),
        average_rtt_ms=400.0,
        total_packets_retransmitted=20,
        total_packets_lost=10,
        status=HealthStatus.CRITICAL,
        message="Critical orphan ENLACE path.",
        maximum_rtt_ms=400.0,
    )

    streaming_health = StreamingHealth(
        captured_at=captured_at,
        paths=(orphan_path,),
        status=HealthStatus.CRITICAL,
        message="Critical specialized SRT evidence.",
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=streaming_health,
    )

    assert health.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )

    assert health.status is HealthStatus.HEALTHY
    assert health.worst_observed_status is HealthStatus.HEALTHY

    assert tuple(
        service.service_id
        for service in health.services
    ) == (
        "IMPACT",
    )

    service = health.services[0]

    assert tuple(
        protocol.protocol
        for protocol in service.protocols
    ) == (
        SessionProtocol.RTMP,
    )


def test_streaming_health_aggregator_rejects_ambiguous_srt_match() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        17,
        30,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="srt-reader-ambiguous",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="active",
        remote_ip="192.0.2.60",
        remote_port=5501,
        path="IMPACT",
        connected_since=captured_at,
        quality=SessionQuality.GOOD,
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=(session,),
    )

    connection_a = SRTConnectionHealth(
        connection_id="srt-reader-ambiguous",
        path_name="IMPACT",
        state="active",
        rtt_ms=250.0,
        packets_retransmitted=5,
        packets_lost=2,
        status=HealthStatus.CRITICAL,
        message="First specialized observation.",
    )

    connection_b = SRTConnectionHealth(
        connection_id="srt-reader-ambiguous",
        path_name="IMPACT",
        state="active",
        rtt_ms=150.0,
        packets_retransmitted=2,
        packets_lost=1,
        status=HealthStatus.DEGRADED,
        message="Second specialized observation.",
    )

    ambiguous_path = SRTPathHealth(
        name="IMPACT",
        connections=(
            connection_a,
            connection_b,
        ),
        average_rtt_ms=200.0,
        total_packets_retransmitted=7,
        total_packets_lost=3,
        status=HealthStatus.CRITICAL,
        message="Ambiguous IMPACT observations.",
        maximum_rtt_ms=250.0,
    )

    streaming_health = StreamingHealth(
        captured_at=captured_at,
        paths=(ambiguous_path,),
        status=HealthStatus.CRITICAL,
        message="Ambiguous specialized SRT evidence.",
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=streaming_health,
    )

    assert health.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )

    assert health.status is HealthStatus.HEALTHY
    assert health.worst_observed_status is HealthStatus.HEALTHY

    service = health.services[0]
    protocol = service.protocols[0]

    assert service.service_id == "IMPACT"
    assert protocol.protocol is SessionProtocol.SRT

    assert protocol.status is HealthStatus.HEALTHY
    assert protocol.worst_observed_status is HealthStatus.HEALTHY


def test_streaming_health_aggregator_maps_missing_path_to_unassigned_service() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        18,
        0,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="rtmp-unassigned-1",
        protocol=SessionProtocol.RTMP,
        role=SessionRole.READER,
        state="active",
        remote_ip="192.0.2.70",
        remote_port=5601,
        path=None,
        connected_since=captured_at,
        quality=SessionQuality.GOOD,
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=SessionSnapshot(
            captured_at=captured_at,
            sessions=(session,),
        ),
        streaming_health=None,
    )

    assert health.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )

    assert health.status is HealthStatus.HEALTHY
    assert health.worst_observed_status is HealthStatus.HEALTHY

    assert len(health.services) == 1

    service = health.services[0]

    assert service.service_id == "(sin path)"
    assert service.status is HealthStatus.HEALTHY

    assert len(service.protocols) == 1

    protocol = service.protocols[0]

    assert protocol.service_id == "(sin path)"
    assert protocol.protocol is SessionProtocol.RTMP
    assert protocol.reader_count == 1
    assert protocol.publisher_count == 0
    assert protocol.unknown_role_count == 0


def test_streaming_health_aggregator_does_not_inherit_srt_path_when_session_path_missing() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        18,
        30,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="srt-unassigned-1",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="active",
        remote_ip="192.0.2.80",
        remote_port=5701,
        path=None,
        connected_since=captured_at,
        quality=SessionQuality.GOOD,
    )

    snapshot = SessionSnapshot(
        captured_at=captured_at,
        sessions=(session,),
    )

    specialized_connection = SRTConnectionHealth(
        connection_id="srt-unassigned-1",
        path_name="IMPACT",
        state="active",
        rtt_ms=350.0,
        packets_retransmitted=12,
        packets_lost=6,
        status=HealthStatus.CRITICAL,
        message="Critical specialized SRT evidence.",
    )

    specialized_path = SRTPathHealth(
        name="IMPACT",
        connections=(specialized_connection,),
        average_rtt_ms=350.0,
        total_packets_retransmitted=12,
        total_packets_lost=6,
        status=HealthStatus.CRITICAL,
        message="Critical IMPACT path.",
        maximum_rtt_ms=350.0,
    )

    streaming_health = StreamingHealth(
        captured_at=captured_at,
        paths=(specialized_path,),
        status=HealthStatus.CRITICAL,
        message="Critical specialized streaming health.",
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=snapshot,
        streaming_health=streaming_health,
    )

    assert health.population == HealthPopulation(
        healthy_count=1,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
    )

    assert health.status is HealthStatus.HEALTHY
    assert health.worst_observed_status is HealthStatus.HEALTHY

    assert len(health.services) == 1

    service = health.services[0]

    assert service.service_id == "(sin path)"
    assert service.status is HealthStatus.HEALTHY
    assert service.worst_observed_status is HealthStatus.HEALTHY

    assert len(service.protocols) == 1

    protocol = service.protocols[0]

    assert protocol.service_id == "(sin path)"
    assert protocol.protocol is SessionProtocol.SRT
    assert protocol.status is HealthStatus.HEALTHY
    assert protocol.worst_observed_status is HealthStatus.HEALTHY
    assert protocol.reader_count == 1


def test_streaming_health_aggregator_preserves_unknown_protocol() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        19,
        0,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="unknown-protocol-1",
        protocol=SessionProtocol.UNKNOWN,
        role=SessionRole.UNKNOWN,
        state="active",
        remote_ip="192.0.2.90",
        remote_port=5801,
        path="IMPACT",
        connected_since=captured_at,
        quality=SessionQuality.FAIR,
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=SessionSnapshot(
            captured_at=captured_at,
            sessions=(session,),
        ),
        streaming_health=None,
    )

    assert health.population == HealthPopulation(
        healthy_count=0,
        degraded_count=1,
        critical_count=0,
        unknown_count=0,
    )

    assert health.status is HealthStatus.DEGRADED
    assert health.worst_observed_status is HealthStatus.DEGRADED

    assert len(health.services) == 1

    service = health.services[0]

    assert service.service_id == "IMPACT"
    assert service.status is HealthStatus.DEGRADED

    assert len(service.protocols) == 1

    protocol = service.protocols[0]

    assert protocol.protocol is SessionProtocol.UNKNOWN
    assert protocol.status is HealthStatus.DEGRADED
    assert protocol.worst_observed_status is HealthStatus.DEGRADED

    assert protocol.reader_count == 0
    assert protocol.publisher_count == 0
    assert protocol.unknown_role_count == 1


def test_streaming_health_aggregator_preserves_critical_with_low_coverage() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        19,
        30,
        tzinfo=UTC,
    )

    sessions = (
        ActiveSession(
            session_id="rtmp-critical-1",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.100",
            remote_port=5901,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.CRITICAL,
        ),
        *tuple(
            ActiveSession(
                session_id=f"rtmp-unknown-{index}",
                protocol=SessionProtocol.RTMP,
                role=SessionRole.READER,
                state="active",
                remote_ip=f"192.0.2.{100 + index}",
                remote_port=5901 + index,
                path="IMPACT",
                connected_since=captured_at,
                quality=SessionQuality.UNKNOWN,
            )
            for index in range(1, 10)
        ),
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=SessionSnapshot(
            captured_at=captured_at,
            sessions=sessions,
        ),
        streaming_health=None,
    )

    assert health.population == HealthPopulation(
        healthy_count=0,
        degraded_count=0,
        critical_count=1,
        unknown_count=9,
    )

    assert health.population.known_count == 1
    assert health.population.total_count == 10
    assert health.population.affected_count == 1
    assert health.population.affected_fraction == 1.0
    assert health.population.evidence_coverage == 0.1

    assert health.status is HealthStatus.CRITICAL
    assert health.worst_observed_status is HealthStatus.CRITICAL

    service = health.services[0]
    protocol = service.protocols[0]

    assert service.status is HealthStatus.CRITICAL
    assert service.worst_observed_status is HealthStatus.CRITICAL

    assert protocol.status is HealthStatus.CRITICAL
    assert protocol.worst_observed_status is HealthStatus.CRITICAL


def test_streaming_health_aggregator_falls_back_when_srt_health_is_empty() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        20,
        0,
        tzinfo=UTC,
    )

    session = ActiveSession(
        session_id="srt-empty-health-1",
        protocol=SessionProtocol.SRT,
        role=SessionRole.READER,
        state="active",
        remote_ip="192.0.2.120",
        remote_port=6001,
        path="IMPACT",
        connected_since=captured_at,
        quality=SessionQuality.FAIR,
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=SessionSnapshot(
            captured_at=captured_at,
            sessions=(session,),
        ),
        streaming_health=StreamingHealth.empty(
            captured_at=captured_at,
        ),
    )

    assert health.population == HealthPopulation(
        healthy_count=0,
        degraded_count=1,
        critical_count=0,
        unknown_count=0,
    )

    assert health.status is HealthStatus.DEGRADED
    assert health.worst_observed_status is HealthStatus.DEGRADED

    service = health.services[0]
    protocol = service.protocols[0]

    assert service.service_id == "IMPACT"
    assert service.status is HealthStatus.DEGRADED
    assert service.worst_observed_status is HealthStatus.DEGRADED

    assert protocol.protocol is SessionProtocol.SRT
    assert protocol.status is HealthStatus.DEGRADED
    assert protocol.worst_observed_status is HealthStatus.DEGRADED
    assert protocol.reader_count == 1


def test_streaming_health_aggregator_escalates_without_healthy_members() -> None:
    captured_at = datetime(
        2026,
        9,
        9,
        20,
        30,
        tzinfo=UTC,
    )

    sessions = (
        ActiveSession(
            session_id="rtmp-degraded-1",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.130",
            remote_port=6101,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.FAIR,
        ),
        ActiveSession(
            session_id="rtmp-critical-1",
            protocol=SessionProtocol.RTMP,
            role=SessionRole.READER,
            state="active",
            remote_ip="192.0.2.131",
            remote_port=6102,
            path="IMPACT",
            connected_since=captured_at,
            quality=SessionQuality.CRITICAL,
        ),
    )

    health = StreamingHealthAggregator().build(
        session_snapshot=SessionSnapshot(
            captured_at=captured_at,
            sessions=sessions,
        ),
        streaming_health=None,
    )

    assert health.population == HealthPopulation(
        healthy_count=0,
        degraded_count=1,
        critical_count=1,
        unknown_count=0,
    )

    assert health.status is HealthStatus.CRITICAL
    assert health.worst_observed_status is HealthStatus.CRITICAL

    service = health.services[0]
    protocol = service.protocols[0]

    assert service.status is HealthStatus.CRITICAL
    assert service.worst_observed_status is HealthStatus.CRITICAL

    assert protocol.status is HealthStatus.CRITICAL
    assert protocol.worst_observed_status is HealthStatus.CRITICAL
