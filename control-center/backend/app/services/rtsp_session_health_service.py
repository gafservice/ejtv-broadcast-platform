"""Servicio temporal especializado de salud RTSP."""

from __future__ import annotations

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming import (
    HealthStatus,
    RTSPSessionHealth,
)


class RTSPSessionHealthService:
    """Construye salud RTSP a partir de observaciones temporales."""

    def build(
        self,
        *,
        previous_snapshot: SessionSnapshot | None,
        current_snapshot: SessionSnapshot,
    ) -> tuple[RTSPSessionHealth, ...]:
        """Construye salud para las sesiones RTSP observadas."""

        sessions: list[RTSPSessionHealth] = []

        for session in current_snapshot.sessions:
            if session.protocol is not SessionProtocol.RTSP:
                continue

            if session.path is None:
                continue

            effective_delta_bytes: int | None = None
            effective_bitrate_mbps: float | None = None
            status = HealthStatus.UNKNOWN
            message = "Insufficient temporal evidence for RTSP session."

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
                    and previous_session.protocol is SessionProtocol.RTSP
                    and previous_session.path == session.path
                    and previous_session.role is session.role
                    and previous_session.connected_since
                    == session.connected_since
                    and interval_seconds > 0
                ):
                    if session.role is SessionRole.PUBLISHER:
                        candidate_delta = (
                            session.bytes_received
                            - previous_session.bytes_received
                        )
                    elif session.role is SessionRole.READER:
                        candidate_delta = (
                            session.bytes_sent
                            - previous_session.bytes_sent
                        )
                    else:
                        candidate_delta = None

                    if (
                        candidate_delta is not None
                        and candidate_delta > 0
                    ):
                        effective_delta_bytes = candidate_delta
                        effective_bitrate_mbps = (
                            candidate_delta
                            * 8
                            / interval_seconds
                            / 1_000_000
                        )

                        status = HealthStatus.HEALTHY
                        message = (
                            "RTSP publisher has observed effective traffic."
                            if session.role is SessionRole.PUBLISHER
                            else "RTSP reader has observed effective traffic."
                        )

            sessions.append(
                RTSPSessionHealth(
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
