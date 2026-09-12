"""Domain models for multiprotocol streaming health aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionQuality,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming.health import (
    HealthStatus,
    RTMPConnectionHealth,
    RTSPSessionHealth,
    StreamingHealth,
)


@dataclass(frozen=True, slots=True)
class HealthPopulation:
    """Population summary grouped by operational health state."""

    healthy_count: int
    degraded_count: int
    critical_count: int
    unknown_count: int

    def __post_init__(self) -> None:
        """Validate that population counters are non-negative."""

        counts = (
            self.healthy_count,
            self.degraded_count,
            self.critical_count,
            self.unknown_count,
        )

        if any(count < 0 for count in counts):
            raise ValueError(
                "Health population counts must be non-negative."
            )

    @property
    def known_count(self) -> int:
        """Return the number of observations with known health."""

        return (
            self.healthy_count
            + self.degraded_count
            + self.critical_count
        )

    @property
    def total_count(self) -> int:
        """Return the complete observed population."""

        return self.known_count + self.unknown_count

    @property
    def affected_count(self) -> int:
        """Return known observations that are degraded or critical."""

        return self.degraded_count + self.critical_count

    @property
    def affected_fraction(self) -> float | None:
        """Return affected share among observations with known health."""

        if self.known_count == 0:
            return None

        return self.affected_count / self.known_count

    @property
    def evidence_coverage(self) -> float | None:
        """Return the share of observed population with known health."""

        if self.total_count == 0:
            return None

        return self.known_count / self.total_count


def resolve_worst_status(
    statuses: tuple["HealthStatus", ...],
) -> "HealthStatus":
    """Return the worst known observed health status."""

    from app.domain.streaming.health import HealthStatus

    if HealthStatus.CRITICAL in statuses:
        return HealthStatus.CRITICAL

    if HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED

    if HealthStatus.HEALTHY in statuses:
        return HealthStatus.HEALTHY

    return HealthStatus.UNKNOWN


def resolve_aggregate_status(
    statuses: tuple["HealthStatus", ...],
) -> "HealthStatus":
    """Resolve operational aggregate health from known observations."""

    from app.domain.streaming.health import HealthStatus

    known_statuses = tuple(
        status
        for status in statuses
        if status is not HealthStatus.UNKNOWN
    )

    if not known_statuses:
        return HealthStatus.UNKNOWN

    if all(
        status is HealthStatus.HEALTHY
        for status in known_statuses
    ):
        return HealthStatus.HEALTHY

    if (
        HealthStatus.HEALTHY not in known_statuses
        and HealthStatus.CRITICAL in known_statuses
    ):
        return HealthStatus.CRITICAL

    return HealthStatus.DEGRADED


@dataclass(frozen=True, slots=True)
class ProtocolHealth:
    """Health summary for one protocol within one service scope."""

    service_id: str
    protocol: "SessionProtocol"
    population: HealthPopulation
    reader_count: int
    publisher_count: int
    unknown_role_count: int
    status: "HealthStatus"
    worst_observed_status: "HealthStatus"
    message: str

    def __post_init__(self) -> None:
        """Validate protocol-health invariants."""

        if not isinstance(self.protocol, SessionProtocol):
            raise ValueError(
                "Protocol health protocol must be a SessionProtocol."
            )

        if not isinstance(self.status, HealthStatus):
            raise ValueError(
                "Protocol health status must be a HealthStatus."
            )

        if not isinstance(
            self.worst_observed_status,
            HealthStatus,
        ):
            raise ValueError(
                "Protocol health worst_observed_status "
                "must be a HealthStatus."
            )

        if not self.service_id.strip():
            raise ValueError(
                "Protocol health service_id must not be blank."
            )

        if not self.message.strip():
            raise ValueError(
                "Protocol health message must not be blank."
            )

        role_counts = (
            self.reader_count,
            self.publisher_count,
            self.unknown_role_count,
        )

        if any(count < 0 for count in role_counts):
            raise ValueError(
                "Protocol health role counts must be non-negative."
            )

        if sum(role_counts) != self.population.total_count:
            raise ValueError(
                "Protocol health role counts must match population total."
            )


@dataclass(frozen=True, slots=True)
class ServiceHealth:
    """Health summary for one logical multimedia service."""

    service_id: str
    protocols: tuple[ProtocolHealth, ...]
    population: HealthPopulation
    status: "HealthStatus"
    worst_observed_status: "HealthStatus"
    message: str

    def __post_init__(self) -> None:
        """Validate service-health invariants."""

        if not isinstance(self.status, HealthStatus):
            raise ValueError(
                "Service health status must be a HealthStatus."
            )

        if not isinstance(
            self.worst_observed_status,
            HealthStatus,
        ):
            raise ValueError(
                "Service health worst_observed_status "
                "must be a HealthStatus."
            )

        if not self.service_id.strip():
            raise ValueError(
                "Service health service_id must not be blank."
            )

        if not self.message.strip():
            raise ValueError(
                "Service health message must not be blank."
            )

        if any(
            protocol.service_id != self.service_id
            for protocol in self.protocols
        ):
            raise ValueError(
                "All protocol health entries must belong to the service."
            )

        protocol_ids = tuple(
            protocol.protocol
            for protocol in self.protocols
        )

        if len(protocol_ids) != len(set(protocol_ids)):
            raise ValueError(
                "Service health protocols must be unique."
            )

        expected_population = HealthPopulation(
            healthy_count=sum(
                protocol.population.healthy_count
                for protocol in self.protocols
            ),
            degraded_count=sum(
                protocol.population.degraded_count
                for protocol in self.protocols
            ),
            critical_count=sum(
                protocol.population.critical_count
                for protocol in self.protocols
            ),
            unknown_count=sum(
                protocol.population.unknown_count
                for protocol in self.protocols
            ),
        )

        if self.population != expected_population:
            raise ValueError(
                "Service health population must equal protocol populations."
            )


@dataclass(frozen=True, slots=True)
class PlatformHealth:
    """Health summary for the observed multimedia platform."""

    captured_at: "datetime"
    services: tuple[ServiceHealth, ...]
    population: HealthPopulation
    status: "HealthStatus"
    worst_observed_status: "HealthStatus"
    message: str

    def __post_init__(self) -> None:
        """Validate platform-health invariants."""

        if not isinstance(self.status, HealthStatus):
            raise ValueError(
                "Platform health status must be a HealthStatus."
            )

        if not isinstance(
            self.worst_observed_status,
            HealthStatus,
        ):
            raise ValueError(
                "Platform health worst_observed_status "
                "must be a HealthStatus."
            )

        if (
            self.captured_at.tzinfo is None
            or self.captured_at.utcoffset() is None
        ):
            raise ValueError(
                "Platform health captured_at must be timezone-aware."
            )

        if not self.message.strip():
            raise ValueError(
                "Platform health message must not be blank."
            )

        service_ids = tuple(
            service.service_id
            for service in self.services
        )

        if len(service_ids) != len(set(service_ids)):
            raise ValueError(
                "Platform health service ids must be unique."
            )

        expected_population = HealthPopulation(
            healthy_count=sum(
                service.population.healthy_count
                for service in self.services
            ),
            degraded_count=sum(
                service.population.degraded_count
                for service in self.services
            ),
            critical_count=sum(
                service.population.critical_count
                for service in self.services
            ),
            unknown_count=sum(
                service.population.unknown_count
                for service in self.services
            ),
        )

        if self.population != expected_population:
            raise ValueError(
                "Platform health population must equal service populations."
            )


class StreamingHealthAggregator:
    """Build hierarchical streaming health from observed session state."""

    def build(
        self,
        *,
        session_snapshot: "SessionSnapshot",
        streaming_health: "StreamingHealth | None",
        rtmp_connections: tuple[RTMPConnectionHealth, ...] = (),
        rtsp_sessions: tuple[RTSPSessionHealth, ...] = (),
    ) -> PlatformHealth:
        """Build platform health from the current observed snapshot."""

        if not session_snapshot.sessions:
            population = HealthPopulation(
                healthy_count=0,
                degraded_count=0,
                critical_count=0,
                unknown_count=0,
            )

            return PlatformHealth(
                captured_at=session_snapshot.captured_at,
                services=(),
                population=population,
                status=HealthStatus.UNKNOWN,
                worst_observed_status=HealthStatus.UNKNOWN,
                message="No active multimedia sessions were observed.",
            )

        protocol_groups: dict[
            tuple[str, object],
            list[tuple[object, HealthStatus]],
        ] = {}

        for session in session_snapshot.sessions:
            service_id = session.path or "(sin path)"
            status = self._status_for_session(
                session=session,
                streaming_health=streaming_health,
                rtmp_connections=rtmp_connections,
                rtsp_sessions=rtsp_sessions,
            )

            key = (
                service_id,
                session.protocol,
            )

            protocol_groups.setdefault(
                key,
                [],
            ).append(
                (
                    session,
                    status,
                )
            )

        protocols_by_service: dict[
            str,
            list[ProtocolHealth],
        ] = {}

        for (
            service_id,
            protocol_id,
        ), entries in protocol_groups.items():
            statuses = tuple(
                status
                for _, status in entries
            )

            population = self._population_from_statuses(
                statuses
            )

            protocol_health = ProtocolHealth(
                service_id=service_id,
                protocol=protocol_id,
                population=population,
                reader_count=sum(
                    session.role is SessionRole.READER
                    for session, _ in entries
                ),
                publisher_count=sum(
                    session.role is SessionRole.PUBLISHER
                    for session, _ in entries
                ),
                unknown_role_count=sum(
                    session.role is SessionRole.UNKNOWN
                    for session, _ in entries
                ),
                status=resolve_aggregate_status(
                    statuses
                ),
                worst_observed_status=resolve_worst_status(
                    statuses
                ),
                message=(
                    f"{protocol_id.value} health for "
                    f"service {service_id}."
                ),
            )

            protocols_by_service.setdefault(
                service_id,
                [],
            ).append(
                protocol_health
            )

        services: list[ServiceHealth] = []

        for service_id in sorted(
            protocols_by_service,
            key=str.casefold,
        ):
            protocols = tuple(
                sorted(
                    protocols_by_service[service_id],
                    key=lambda item: item.protocol.value.casefold(),
                )
            )

            population = self._population_from_protocols(
                protocols
            )

            statuses = tuple(
                protocol.status
                for protocol in protocols
            )

            services.append(
                ServiceHealth(
                    service_id=service_id,
                    protocols=protocols,
                    population=population,
                    status=resolve_aggregate_status(
                        statuses
                    ),
                    worst_observed_status=resolve_worst_status(
                        tuple(
                            protocol.worst_observed_status
                            for protocol in protocols
                        )
                    ),
                    message=f"Service {service_id} health.",
                )
            )

        ordered_services = tuple(services)

        platform_population = self._population_from_services(
            ordered_services
        )

        return PlatformHealth(
            captured_at=session_snapshot.captured_at,
            services=ordered_services,
            population=platform_population,
            status=resolve_aggregate_status(
                tuple(
                    service.status
                    for service in ordered_services
                )
            ),
            worst_observed_status=resolve_worst_status(
                tuple(
                    service.worst_observed_status
                    for service in ordered_services
                )
            ),
            message="Observed multimedia platform health.",
        )

    @classmethod
    def _status_for_session(
        cls,
        *,
        session: ActiveSession,
        streaming_health: StreamingHealth | None,
        rtmp_connections: tuple[RTMPConnectionHealth, ...],
        rtsp_sessions: tuple[RTSPSessionHealth, ...],
    ) -> HealthStatus:
        if (
            session.protocol is SessionProtocol.SRT
            and streaming_health is not None
        ):
            specialized_status = cls._matching_srt_status(
                session=session,
                streaming_health=streaming_health,
            )

            if specialized_status is not None:
                return specialized_status

        if session.protocol is SessionProtocol.RTMP:
            specialized_status = cls._matching_rtmp_status(
                session=session,
                rtmp_connections=rtmp_connections,
            )

            if specialized_status is not None:
                return specialized_status

        if session.protocol is SessionProtocol.RTSP:
            specialized_status = cls._matching_rtsp_status(
                session=session,
                rtsp_sessions=rtsp_sessions,
            )

            if specialized_status is not None:
                return specialized_status

        return cls._status_from_session_quality(
            session.quality
        )

    @staticmethod
    def _matching_srt_status(
        *,
        session: ActiveSession,
        streaming_health: StreamingHealth,
    ) -> HealthStatus | None:
        matches = tuple(
            connection
            for path in streaming_health.paths
            for connection in path.connections
            if (
                connection.connection_id == session.session_id
                and session.path is not None
                and connection.path_name == session.path
            )
        )

        if len(matches) != 1:
            return None

        return matches[0].status

    @staticmethod
    def _matching_rtmp_status(
        *,
        session: ActiveSession,
        rtmp_connections: tuple[RTMPConnectionHealth, ...],
    ) -> HealthStatus | None:
        matches = tuple(
            connection
            for connection in rtmp_connections
            if (
                connection.connection_id == session.session_id
                and session.path is not None
                and connection.path_name == session.path
            )
        )

        if len(matches) != 1:
            return None

        return matches[0].status

    @staticmethod
    def _matching_rtsp_status(
        *,
        session: ActiveSession,
        rtsp_sessions: tuple[RTSPSessionHealth, ...],
    ) -> HealthStatus | None:
        matches = tuple(
            rtsp_session
            for rtsp_session in rtsp_sessions
            if (
                rtsp_session.session_id == session.session_id
                and session.path is not None
                and rtsp_session.path_name == session.path
            )
        )

        if len(matches) != 1:
            return None

        return matches[0].status

    @staticmethod
    def _status_from_session_quality(
        quality: SessionQuality,
    ) -> HealthStatus:
        if quality in (
            SessionQuality.EXCELLENT,
            SessionQuality.GOOD,
        ):
            return HealthStatus.HEALTHY

        if quality in (
            SessionQuality.FAIR,
            SessionQuality.POOR,
        ):
            return HealthStatus.DEGRADED

        if quality is SessionQuality.CRITICAL:
            return HealthStatus.CRITICAL

        return HealthStatus.UNKNOWN

    @staticmethod
    def _population_from_statuses(
        statuses: tuple[HealthStatus, ...],
    ) -> HealthPopulation:
        return HealthPopulation(
            healthy_count=sum(
                status is HealthStatus.HEALTHY
                for status in statuses
            ),
            degraded_count=sum(
                status is HealthStatus.DEGRADED
                for status in statuses
            ),
            critical_count=sum(
                status is HealthStatus.CRITICAL
                for status in statuses
            ),
            unknown_count=sum(
                status is HealthStatus.UNKNOWN
                for status in statuses
            ),
        )

    @staticmethod
    def _population_from_protocols(
        protocols: tuple[ProtocolHealth, ...],
    ) -> HealthPopulation:
        return HealthPopulation(
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

    @staticmethod
    def _population_from_services(
        services: tuple[ServiceHealth, ...],
    ) -> HealthPopulation:
        return HealthPopulation(
            healthy_count=sum(
                service.population.healthy_count
                for service in services
            ),
            degraded_count=sum(
                service.population.degraded_count
                for service in services
            ),
            critical_count=sum(
                service.population.critical_count
                for service in services
            ),
            unknown_count=sum(
                service.population.unknown_count
                for service in services
            ),
        )
