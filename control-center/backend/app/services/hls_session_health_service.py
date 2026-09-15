"""Servicio temporal especializado de salud HLS."""

from __future__ import annotations

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming import (
    HealthStatus,
    HLSSessionHealth,
)


class HLSSessionHealthService:
    """Construye salud HLS a partir de observaciones temporales."""

    def build(
        self,
        *,
        previous_snapshot: SessionSnapshot | None,
        current_snapshot: SessionSnapshot,
    ) -> tuple[HLSSessionHealth, ...]:
        """Construye salud para las sesiones HLS observadas."""

        sessions: list[HLSSessionHealth] = []

        for session in current_snapshot.sessions:
            if session.protocol is not SessionProtocol.HLS:
                continue

            if session.path is None:
                continue

            effective_delta_bytes: int | None = None
            effective_bitrate_mbps: float | None = None
            status = HealthStatus.UNKNOWN
            message = "Insufficient temporal evidence for HLS session."

            if previous_snapshot is not None:
                previous_session = previous_snapshot.get_session(
                    session.session_id
                )

                interval_seconds = (
                    current_snapshot.captured_at
                    - previous_snapshot.captured_at
                ).total_seconds()

                if (
                    previous_session is not None
                    and previous_session.protocol is SessionProtocol.HLS
                    and previous_session.path == session.path
                    and previous_session.role is session.role
                    and previous_session.connected_since
                    == session.connected_since
                    and interval_seconds > 0
                    and session.role is SessionRole.READER
                ):
                    candidate_delta = (
                        session.bytes_sent
                        - previous_session.bytes_sent
                    )

                    if candidate_delta > 0:
                        effective_delta_bytes = candidate_delta
                        effective_bitrate_mbps = (
                            candidate_delta
                            * 8
                            / interval_seconds
                            / 1_000_000
                        )

                        status = HealthStatus.HEALTHY
                        message = (
                            "HLS reader has observed effective traffic."
                        )

            sessions.append(
                HLSSessionHealth(
                    session_id=session.session_id,
                    path_name=session.path,
                    state=session.state,
                    effective_delta_bytes=effective_delta_bytes,
                    effective_bitrate_mbps=effective_bitrate_mbps,
                    status=status,
                    message=message,
                )
            )

        return tuple(sessions)
