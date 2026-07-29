"""Mediciones derivadas para sesiones multimedia activas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import ActiveSession
from .protocol import SessionProtocol
from .quality import SessionQuality


@dataclass(frozen=True, slots=True)
class SessionPathSummary:
    """Resumen agregado de sesiones asociadas a un path."""

    path: str
    session_count: int
    reader_count: int
    publisher_count: int
    inbound_bitrate_mbps: float
    outbound_bitrate_mbps: float
    degraded_session_count: int
    worst_quality: SessionQuality

    def __post_init__(self) -> None:
        """Valida invariantes del resumen por path."""

        if not self.path.strip():
            raise ValueError("path no puede estar vacío.")

        integer_values = (
            self.session_count,
            self.reader_count,
            self.publisher_count,
            self.degraded_session_count,
        )

        if any(value < 0 for value in integer_values):
            raise ValueError(
                "Los contadores del resumen por path no pueden ser negativos."
            )

        if self.reader_count + self.publisher_count > self.session_count:
            raise ValueError(
                "reader_count + publisher_count no puede superar "
                "session_count."
            )

        if self.degraded_session_count > self.session_count:
            raise ValueError(
                "degraded_session_count no puede superar session_count."
            )

        if self.inbound_bitrate_mbps < 0:
            raise ValueError(
                "inbound_bitrate_mbps no puede ser negativo."
            )

        if self.outbound_bitrate_mbps < 0:
            raise ValueError(
                "outbound_bitrate_mbps no puede ser negativo."
            )


@dataclass(frozen=True, slots=True)
class SessionMeasurement:
    """Vista agregada de las sesiones activas para consumo del NOC."""

    captured_at: datetime
    sessions: tuple[ActiveSession, ...]
    paths: tuple[SessionPathSummary, ...]

    total_sessions: int
    reader_count: int
    publisher_count: int
    unknown_role_count: int

    degraded_session_count: int
    critical_session_count: int

    total_inbound_bitrate_mbps: float
    total_outbound_bitrate_mbps: float

    worst_quality: SessionQuality
    protocols: tuple[SessionProtocol, ...]

    def __post_init__(self) -> None:
        """Valida invariantes generales de la medición."""

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at debe contener información de zona horaria."
            )

        integer_values = (
            self.total_sessions,
            self.reader_count,
            self.publisher_count,
            self.unknown_role_count,
            self.degraded_session_count,
            self.critical_session_count,
        )

        if any(value < 0 for value in integer_values):
            raise ValueError(
                "Los contadores de sesión no pueden ser negativos."
            )

        if len(self.sessions) != self.total_sessions:
            raise ValueError(
                "total_sessions debe coincidir con la cantidad de sesiones."
            )

        classified_roles = (
            self.reader_count
            + self.publisher_count
            + self.unknown_role_count
        )

        if classified_roles != self.total_sessions:
            raise ValueError(
                "La suma de roles debe coincidir con total_sessions."
            )

        if self.degraded_session_count > self.total_sessions:
            raise ValueError(
                "degraded_session_count no puede superar total_sessions."
            )

        if self.critical_session_count > self.degraded_session_count:
            raise ValueError(
                "critical_session_count no puede superar "
                "degraded_session_count."
            )

        if self.total_inbound_bitrate_mbps < 0:
            raise ValueError(
                "total_inbound_bitrate_mbps no puede ser negativo."
            )

        if self.total_outbound_bitrate_mbps < 0:
            raise ValueError(
                "total_outbound_bitrate_mbps no puede ser negativo."
            )

        session_ids = [
            session.session_id
            for session in self.sessions
        ]

        if len(session_ids) != len(set(session_ids)):
            raise ValueError(
                "SessionMeasurement no admite session_id duplicados."
            )

        path_names = [
            path.path
            for path in self.paths
        ]

        if len(path_names) != len(set(path_names)):
            raise ValueError(
                "SessionMeasurement no admite paths duplicados."
            )

    @property
    def has_degraded_sessions(self) -> bool:
        """Indica si existen sesiones con calidad FAIR o peor."""

        return self.degraded_session_count > 0

    @property
    def has_critical_sessions(self) -> bool:
        """Indica si existen sesiones críticas."""

        return self.critical_session_count > 0

    @property
    def protocol_counts(
        self,
    ) -> tuple[tuple[SessionProtocol, int], ...]:
        """Cantidad de sesiones activas agrupadas por protocolo."""

        return tuple(
            (
                protocol,
                sum(
                    session.protocol is protocol
                    for session in self.sessions
                ),
            )
            for protocol in SessionProtocol
        )
