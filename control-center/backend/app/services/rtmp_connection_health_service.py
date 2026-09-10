"""Servicio temporal especializado de salud RTMP."""

from __future__ import annotations

from app.domain.sessions import (
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
)
from app.domain.streaming import HealthStatus, RTMPConnectionHealth


class RTMPConnectionHealthService:
    """Construye salud RTMP a partir de observaciones temporales."""

    def build(
        self,
        *,
        previous_snapshot: SessionSnapshot | None,
        current_snapshot: SessionSnapshot,
    ) -> tuple[RTMPConnectionHealth, ...]:
        """Construye salud para las conexiones RTMP observadas."""

        connections: list[RTMPConnectionHealth] = []

        for session in current_snapshot.sessions:
            if session.protocol is not SessionProtocol.RTMP:
                continue

            if session.path is None:
                continue

            effective_delta_bytes: int | None = None
            effective_bitrate_mbps: float | None = None
            status = HealthStatus.UNKNOWN
            message = "Insufficient temporal evidence for RTMP connection."

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
                    and previous_session.protocol is SessionProtocol.RTMP
                    and previous_session.path == session.path
                    and previous_session.role is session.role
                    and previous_session.connected_since == session.connected_since
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

                    if candidate_delta is not None and candidate_delta > 0:
                        effective_delta_bytes = candidate_delta
                        effective_bitrate_mbps = (
                            candidate_delta
                            * 8
                            / interval_seconds
                            / 1_000_000
                        )
                        status = HealthStatus.HEALTHY
                        message = (
                            "RTMP publisher has observed effective traffic."
                            if session.role is SessionRole.PUBLISHER
                            else "RTMP reader has observed effective traffic."
                        )

            connections.append(
                RTMPConnectionHealth(
                    connection_id=session.session_id,
                    path_name=session.path,
                    state=session.state,
                    effective_delta_bytes=effective_delta_bytes,
                    effective_bitrate_mbps=effective_bitrate_mbps,
                    outbound_frames_discarded=None,
                    status=status,
                    message=message,
                )
            )

        return tuple(connections)
