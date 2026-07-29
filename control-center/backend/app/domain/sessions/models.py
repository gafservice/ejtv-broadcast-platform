"""Modelos de dominio para sesiones multimedia activas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from ipaddress import ip_address

from .protocol import SessionProtocol, SessionRole
from .quality import SessionQuality


@dataclass(frozen=True, slots=True)
class ActiveSession:
    """Representación normalizada de una sesión multimedia activa."""

    session_id: str
    protocol: SessionProtocol
    role: SessionRole
    state: str

    remote_ip: str
    remote_port: int | None

    path: str | None
    connected_since: datetime

    username: str | None = None
    user_agent: str | None = None

    country_code: str | None = None
    country_name: str | None = None

    asn: int | None = None
    provider: str | None = None

    bytes_received: int = 0
    bytes_sent: int = 0

    bitrate_receive_mbps: float | None = None
    bitrate_send_mbps: float | None = None
    link_capacity_mbps: float | None = None

    rtt_ms: float | None = None
    packet_loss_rate: float | None = None
    retransmission_rate: float | None = None

    packets_received: int = 0
    packets_sent: int = 0
    packets_lost: int = 0
    packets_retransmitted: int = 0

    quality: SessionQuality = SessionQuality.UNKNOWN

    def __post_init__(self) -> None:
        """Valida invariantes básicas del modelo."""

        if not self.session_id.strip():
            raise ValueError("session_id no puede estar vacío.")

        if not self.remote_ip.strip():
            raise ValueError("remote_ip no puede estar vacío.")

        try:
            ip_address(self.remote_ip)
        except ValueError as exc:
            raise ValueError(
                f"remote_ip no contiene una dirección válida: "
                f"{self.remote_ip}"
            ) from exc

        if self.remote_port is not None and not (
            1 <= self.remote_port <= 65_535
        ):
            raise ValueError(
                "remote_port debe estar entre 1 y 65535."
            )

        if self.connected_since.tzinfo is None:
            raise ValueError(
                "connected_since debe contener información de zona horaria."
            )

        integer_counters = (
            self.bytes_received,
            self.bytes_sent,
            self.packets_received,
            self.packets_sent,
            self.packets_lost,
            self.packets_retransmitted,
        )

        if any(value < 0 for value in integer_counters):
            raise ValueError(
                "Los contadores de sesión no pueden ser negativos."
            )

        optional_metrics = (
            self.bitrate_receive_mbps,
            self.bitrate_send_mbps,
            self.link_capacity_mbps,
            self.rtt_ms,
            self.packet_loss_rate,
            self.retransmission_rate,
        )

        if any(
            value is not None and value < 0
            for value in optional_metrics
        ):
            raise ValueError(
                "Las métricas de sesión no pueden ser negativas."
            )

    @property
    def remote_address(self) -> str:
        """Dirección remota completa en formato IP:puerto."""

        if self.remote_port is None:
            return self.remote_ip

        if ":" in self.remote_ip:
            return f"[{self.remote_ip}]:{self.remote_port}"

        return f"{self.remote_ip}:{self.remote_port}"

    @property
    def is_reader(self) -> bool:
        """Indica si la sesión consume contenido."""

        return self.role is SessionRole.READER

    @property
    def is_publisher(self) -> bool:
        """Indica si la sesión publica contenido."""

        return self.role is SessionRole.PUBLISHER

    @property
    def is_private_network(self) -> bool:
        """Indica si la dirección pertenece a una red privada."""

        return ip_address(self.remote_ip).is_private

    @property
    def is_loopback(self) -> bool:
        """Indica si la conexión proviene del propio servidor."""

        return ip_address(self.remote_ip).is_loopback

    @property
    def location_label(self) -> str:
        """Ubicación disponible para presentar en el dashboard."""

        if self.is_loopback:
            return "Servidor local"

        if self.is_private_network:
            return "Red local"

        if self.country_name:
            return self.country_name

        if self.country_code:
            return self.country_code.upper()

        return "Desconocido"

    def duration_seconds(
        self,
        *,
        now: datetime | None = None,
    ) -> float:
        """Calcula la duración actual de la sesión en segundos."""

        current_time = now or datetime.now(UTC)

        if current_time.tzinfo is None:
            raise ValueError(
                "now debe contener información de zona horaria."
            )

        elapsed = (
            current_time.astimezone(UTC)
            - self.connected_since.astimezone(UTC)
        ).total_seconds()

        return max(0.0, elapsed)

    @property
    def effective_bitrate_mbps(self) -> float | None:
        """Retorna el bitrate correspondiente al rol de la sesión."""

        if self.is_reader:
            return self.bitrate_send_mbps

        if self.is_publisher:
            return self.bitrate_receive_mbps

        if self.bitrate_send_mbps is not None:
            return self.bitrate_send_mbps

        return self.bitrate_receive_mbps


@dataclass(frozen=True, slots=True)
class SessionSnapshot:
    """Colección de sesiones capturadas en un instante."""

    captured_at: datetime
    sessions: tuple[ActiveSession, ...]

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at debe contener información de zona horaria."
            )

        identifiers = [
            session.session_id
            for session in self.sessions
        ]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "SessionSnapshot no admite session_id duplicados."
            )

    @classmethod
    def empty(cls) -> "SessionSnapshot":
        """Construye un snapshot vacío."""

        return cls(
            captured_at=datetime.now(UTC),
            sessions=(),
        )

    @property
    def session_count(self) -> int:
        """Cantidad total de sesiones."""

        return len(self.sessions)

    @property
    def reader_count(self) -> int:
        """Cantidad de sesiones lectoras."""

        return sum(session.is_reader for session in self.sessions)

    @property
    def publisher_count(self) -> int:
        """Cantidad de sesiones publicadoras."""

        return sum(
            session.is_publisher
            for session in self.sessions
        )

    @property
    def protocols(self) -> tuple[SessionProtocol, ...]:
        """Protocolos presentes, ordenados por nombre."""

        return tuple(
            sorted(
                {
                    session.protocol
                    for session in self.sessions
                },
                key=lambda protocol: protocol.value,
            )
        )

    def get_session(
        self,
        session_id: str,
    ) -> ActiveSession | None:
        """Busca una sesión por identificador."""

        return next(
            (
                session
                for session in self.sessions
                if session.session_id == session_id
            ),
            None,
        )
