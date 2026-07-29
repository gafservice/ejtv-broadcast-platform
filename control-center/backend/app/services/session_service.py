"""Servicios de aplicación para mediciones de sesiones multimedia."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from app.domain.sessions import (
    ActiveSession,
    SessionMeasurement,
    SessionPathSummary,
    SessionQuality,
    SessionSnapshot,
)


class SessionService:
    """Genera mediciones agregadas a partir de sesiones activas."""

    UNASSIGNED_PATH = "(sin path)"

    _QUALITY_SEVERITY = {
        SessionQuality.EXCELLENT: 0,
        SessionQuality.GOOD: 1,
        SessionQuality.FAIR: 2,
        SessionQuality.POOR: 3,
        SessionQuality.CRITICAL: 4,
    }

    _DEGRADED_QUALITIES = {
        SessionQuality.FAIR,
        SessionQuality.POOR,
        SessionQuality.CRITICAL,
    }

    def measure(
        self,
        snapshot: SessionSnapshot,
    ) -> SessionMeasurement:
        """Construye una medición agregada para consumo del NOC."""

        sessions = tuple(
            sorted(
                snapshot.sessions,
                key=self._session_sort_key,
            )
        )

        degraded_sessions = tuple(
            session
            for session in sessions
            if self._is_degraded(session)
        )

        critical_session_count = sum(
            session.quality is SessionQuality.CRITICAL
            for session in sessions
        )

        total_inbound_bitrate_mbps = sum(
            session.bitrate_receive_mbps or 0.0
            for session in sessions
        )

        total_outbound_bitrate_mbps = sum(
            session.bitrate_send_mbps or 0.0
            for session in sessions
        )

        return SessionMeasurement(
            captured_at=snapshot.captured_at,
            sessions=sessions,
            paths=self._build_path_summaries(sessions),
            total_sessions=len(sessions),
            reader_count=sum(
                session.is_reader
                for session in sessions
            ),
            publisher_count=sum(
                session.is_publisher
                for session in sessions
            ),
            unknown_role_count=sum(
                not session.is_reader and not session.is_publisher
                for session in sessions
            ),
            degraded_session_count=len(degraded_sessions),
            critical_session_count=critical_session_count,
            total_inbound_bitrate_mbps=total_inbound_bitrate_mbps,
            total_outbound_bitrate_mbps=total_outbound_bitrate_mbps,
            worst_quality=self._resolve_worst_quality(sessions),
            protocols=snapshot.protocols,
        )

    def _build_path_summaries(
        self,
        sessions: tuple[ActiveSession, ...],
    ) -> tuple[SessionPathSummary, ...]:
        """Agrupa las sesiones por path y genera sus resúmenes."""

        grouped_sessions: dict[str, list[ActiveSession]] = defaultdict(list)

        for session in sessions:
            path = session.path or self.UNASSIGNED_PATH
            grouped_sessions[path].append(session)

        return tuple(
            self._build_path_summary(
                path=path,
                sessions=tuple(path_sessions),
            )
            for path, path_sessions in sorted(
                grouped_sessions.items(),
                key=lambda item: item[0].casefold(),
            )
        )

    def _build_path_summary(
        self,
        *,
        path: str,
        sessions: tuple[ActiveSession, ...],
    ) -> SessionPathSummary:
        """Construye el resumen de un único path."""

        return SessionPathSummary(
            path=path,
            session_count=len(sessions),
            reader_count=sum(
                session.is_reader
                for session in sessions
            ),
            publisher_count=sum(
                session.is_publisher
                for session in sessions
            ),
            inbound_bitrate_mbps=sum(
                session.bitrate_receive_mbps or 0.0
                for session in sessions
            ),
            outbound_bitrate_mbps=sum(
                session.bitrate_send_mbps or 0.0
                for session in sessions
            ),
            degraded_session_count=sum(
                self._is_degraded(session)
                for session in sessions
            ),
            worst_quality=self._resolve_worst_quality(sessions),
        )

    @classmethod
    def _resolve_worst_quality(
        cls,
        sessions: Iterable[ActiveSession],
    ) -> SessionQuality:
        """Retorna la peor calidad conocida entre las sesiones."""

        known_qualities = [
            session.quality
            for session in sessions
            if session.quality is not SessionQuality.UNKNOWN
        ]

        if not known_qualities:
            return SessionQuality.UNKNOWN

        return max(
            known_qualities,
            key=lambda quality: cls._QUALITY_SEVERITY[quality],
        )

    @classmethod
    def _is_degraded(
        cls,
        session: ActiveSession,
    ) -> bool:
        """Indica si una sesión requiere atención operativa."""

        return session.quality in cls._DEGRADED_QUALITIES

    @classmethod
    def _session_sort_key(
        cls,
        session: ActiveSession,
    ) -> tuple[int, str, str, str, str, int, str]:
        """Genera un criterio determinista para ordenar las sesiones."""

        quality_severity = cls._QUALITY_SEVERITY.get(
            session.quality,
            -1,
        )

        return (
            -quality_severity,
            (session.path or cls.UNASSIGNED_PATH).casefold(),
            session.protocol.value.casefold(),
            session.role.value.casefold(),
            session.remote_ip,
            session.remote_port or 0,
            session.session_id,
        )
