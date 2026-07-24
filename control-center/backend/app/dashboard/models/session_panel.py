"""Modelo de presentación para el panel ACTIVE CLIENTS."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SessionPanelData:
    """Resumen de sesiones activas listo para el dashboard."""

    total_sessions: int
    readers: int
    publishers: int
    degraded_sessions: int
    critical_sessions: int
    inbound_bitrate_bps: float | None
    outbound_bitrate_bps: float | None
    quality: str
