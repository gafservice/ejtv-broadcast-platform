"""Protocolos y roles normalizados para sesiones multimedia."""

from enum import StrEnum


class SessionProtocol(StrEnum):
    """Protocolo utilizado por una sesión multimedia."""

    SRT = "SRT"
    RTMP = "RTMP"
    RTSP = "RTSP"
    HLS = "HLS"
    WEBRTC = "WebRTC"
    UNKNOWN = "UNKNOWN"


class SessionRole(StrEnum):
    """Rol operativo desempeñado por una sesión."""

    READER = "READER"
    PUBLISHER = "PUBLISHER"
    UNKNOWN = "UNKNOWN"
