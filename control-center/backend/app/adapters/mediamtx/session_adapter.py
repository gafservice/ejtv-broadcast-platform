"""Adaptador de sesiones entre MediaMTX y el dominio."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from app.domain.sessions import (
    ActiveSession,
    SessionProtocol,
    SessionRole,
    SessionSnapshot,
    evaluate_session_quality,
)

from .exceptions import MediaMTXInvalidResponseError
from .session_client import MediaMTXSessionClient
from app.services.geoip_service import GeoIPService


class MediaMTXSessionAdapter:
    """Transforma sesiones de MediaMTX en objetos del dominio."""

    def __init__(
        self,
        client: MediaMTXSessionClient,
        geoip_service: GeoIPService | None = None,
    ) -> None:
        self._client = client
        self._geoip = geoip_service

    def get_snapshot(self) -> SessionSnapshot:
        """Obtiene el snapshot agregado de sesiones activas.

        Inicialmente utiliza únicamente las conexiones SRT. Este punto
        único permitirá agregar otros protocolos sin modificar la capa
        de aplicación.
        """

        return self.get_srt_snapshot()

    def get_srt_snapshot(self) -> SessionSnapshot:
        """Obtiene y normaliza las conexiones SRT activas."""

        payload = self._client.get_srt_connections()

        return self._parse_collection(
            payload=payload,
            protocol=SessionProtocol.SRT,
        )

    def _parse_collection(
        self,
        *,
        payload: Mapping[str, Any],
        protocol: SessionProtocol,
    ) -> SessionSnapshot:
        """Transforma una colección de sesiones en un snapshot."""

        raw_items = payload.get("items", [])

        if not isinstance(raw_items, list):
            raise MediaMTXInvalidResponseError(
                "El campo 'items' de sesiones debe ser una lista."
            )

        sessions = tuple(
            self._parse_session(
                item=item,
                protocol=protocol,
            )
            for item in raw_items
            if isinstance(item, Mapping)
        )

        if len(sessions) != len(raw_items):
            raise MediaMTXInvalidResponseError(
                "Uno o más elementos de sesiones no son objetos válidos."
            )

        return SessionSnapshot(
            captured_at=datetime.now(UTC),
            sessions=sessions,
        )

    def _parse_session(
        self,
        *,
        item: Mapping[str, Any],
        protocol: SessionProtocol,
    ) -> ActiveSession:
        """Normaliza una conexión individual de MediaMTX."""

        session_id = self._required_string(item, "id")
        remote_ip, remote_port = self._parse_remote_address(
            self._required_string(item, "remoteAddr")
        )

        geoip = (
            self._geoip.resolve(remote_ip)
            if self._geoip is not None
            else None
        )

        state = self._optional_string(item.get("state")) or "unknown"
        role = self._resolve_role(state)

        connected_since = self._parse_required_datetime(
            item.get("created"),
            field_name="created",
        )

        packets_received = self._safe_int(
            self._first_available(
                item,
                "packetsReceived",
                "recvPackets",
            )
        )
        packets_sent = self._safe_int(
            self._first_available(
                item,
                "packetsSent",
                "sentPackets",
            )
        )

        packets_lost = self._safe_int(
            self._first_available(
                item,
                "packetsLost",
                "packetsSendLoss",
                "packetsReceivedLoss",
                "packetLoss",
                "lostPackets",
            )
        )

        packets_retransmitted = self._safe_int(
            self._first_available(
                item,
                "packetsRetransmitted",
                "packetsRetrans",
                "packetsReceivedRetrans",
                "retransmissions",
                "retransPackets",
            )
        )

        packet_loss_rate = self._calculate_percentage(
            numerator=packets_lost,
            denominator=self._loss_denominator(
                packets_received=packets_received,
                packets_sent=packets_sent,
                packets_lost=packets_lost,
                role=role,
            ),
        )

        retransmission_rate = self._calculate_percentage(
            numerator=packets_retransmitted,
            denominator=packets_sent,
        )

        rtt_ms = self._safe_optional_float(
            self._first_available(
                item,
                "msRTT",
                "rtt",
                "rttMs",
            )
        )

        quality = evaluate_session_quality(
            rtt_ms=rtt_ms,
            packet_loss_rate=packet_loss_rate,
            retransmission_rate=retransmission_rate,
        )

        return ActiveSession(
            session_id=session_id,
            protocol=protocol,
            role=role,
            state=state,
            remote_ip=remote_ip,
            remote_port=remote_port,
            path=self._optional_string(item.get("path")),
            connected_since=connected_since,
            username=self._optional_string(item.get("user")),
            user_agent=self._optional_string(
                self._first_available(
                    item,
                    "userAgent",
                    "agent",
                )
            ),
            bytes_received=self._safe_int(
                self._first_available(
                    item,
                    "bytesReceived",
                    "recvBytes",
                )
            ),
            bytes_sent=self._safe_int(
                self._first_available(
                    item,
                    "bytesSent",
                    "sentBytes",
                )
            ),
            bitrate_receive_mbps=self._safe_optional_float(
                self._first_available(
                    item,
                    "mbpsReceiveRate",
                    "receiveRate",
                )
            ),
            bitrate_send_mbps=self._safe_optional_float(
                self._first_available(
                    item,
                    "mbpsSendRate",
                    "sendRate",
                )
            ),
            link_capacity_mbps=self._safe_optional_float(
                self._first_available(
                    item,
                    "mbpsLinkCapacity",
                    "linkCapacity",
                )
            ),
            rtt_ms=rtt_ms,
            packet_loss_rate=packet_loss_rate,
            retransmission_rate=retransmission_rate,
            packets_received=packets_received,
            packets_sent=packets_sent,
            packets_lost=packets_lost,
            packets_retransmitted=packets_retransmitted,
            
           country_code=(
                geoip.country_code
                if geoip is not None
                else None
            ),
            country_name=(
                geoip.country_name
                if geoip is not None
                else None
            ),
            asn=(
                geoip.asn
                if geoip is not None
                else None
            ),
            provider=(
                geoip.asn_organization
                if geoip is not None
                else None
            ),
            quality=quality,
        )

    @staticmethod
    def _resolve_role(state: str) -> SessionRole:
        """Determina el rol operativo a partir del estado MediaMTX."""

        normalized = state.strip().lower()

        if normalized in {
            "publish",
            "publisher",
            "publishing",
        }:
            return SessionRole.PUBLISHER

        if normalized in {
            "read",
            "reader",
            "reading",
        }:
            return SessionRole.READER

        return SessionRole.UNKNOWN

    @staticmethod
    def _parse_remote_address(
        remote_address: str,
    ) -> tuple[str, int | None]:
        """Separa IP y puerto de una dirección remota."""

        value = remote_address.strip()

        if not value:
            raise MediaMTXInvalidResponseError(
                "remoteAddr no puede estar vacío."
            )

        if value.startswith("["):
            closing_bracket = value.find("]")

            if closing_bracket == -1:
                raise MediaMTXInvalidResponseError(
                    f"Dirección IPv6 inválida: {value}"
                )

            host = value[1:closing_bracket]
            remainder = value[closing_bracket + 1 :]

            if not remainder:
                return host, None

            if not remainder.startswith(":"):
                raise MediaMTXInvalidResponseError(
                    f"Dirección IPv6 inválida: {value}"
                )

            return host, MediaMTXSessionAdapter._parse_port(
                remainder[1:]
            )

        host, separator, raw_port = value.rpartition(":")

        if not separator:
            return value, None

        if ":" in host:
            # IPv6 sin puerto y sin corchetes.
            return value, None

        if not host:
            raise MediaMTXInvalidResponseError(
                f"Dirección remota inválida: {value}"
            )

        return host, MediaMTXSessionAdapter._parse_port(raw_port)

    @staticmethod
    def _parse_port(raw_port: str) -> int:
        """Convierte y valida un puerto de red."""

        try:
            port = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise MediaMTXInvalidResponseError(
                f"Puerto remoto inválido: {raw_port}"
            ) from exc

        if not 1 <= port <= 65_535:
            raise MediaMTXInvalidResponseError(
                f"Puerto remoto fuera de rango: {port}"
            )

        return port

    @staticmethod
    def _parse_required_datetime(
        value: object,
        *,
        field_name: str,
    ) -> datetime:
        """Convierte una fecha ISO 8601 obligatoria."""

        if not isinstance(value, str) or not value.strip():
            raise MediaMTXInvalidResponseError(
                f"El campo '{field_name}' debe contener una fecha."
            )

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"

        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise MediaMTXInvalidResponseError(
                f"El campo '{field_name}' contiene una fecha inválida."
            ) from exc

        if parsed.tzinfo is None:
            raise MediaMTXInvalidResponseError(
                f"El campo '{field_name}' debe incluir zona horaria."
            )

        return parsed.astimezone(UTC)

    @staticmethod
    def _required_string(
        item: Mapping[str, Any],
        field_name: str,
    ) -> str:
        """Obtiene un texto obligatorio."""

        value = item.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise MediaMTXInvalidResponseError(
                f"El campo '{field_name}' debe contener texto."
            )

        return value.strip()

    @staticmethod
    def _optional_string(value: object) -> str | None:
        """Normaliza un texto opcional."""

        if not isinstance(value, str):
            return None

        normalized = value.strip()

        return normalized or None

    @staticmethod
    def _safe_int(
        value: object,
        *,
        default: int = 0,
    ) -> int:
        """Convierte un contador no negativo."""

        if value is None:
            return default

        if isinstance(value, bool):
            return default

        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            return default

        return max(0, numeric_value)

    @staticmethod
    def _safe_optional_float(
        value: object,
    ) -> float | None:
        """Convierte una métrica opcional no negativa."""

        if value is None or isinstance(value, bool):
            return None

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return None

        if numeric_value < 0:
            return None

        return numeric_value

    @staticmethod
    def _first_available(
        item: Mapping[str, Any],
        *field_names: str,
    ) -> object:
        """Retorna el primer campo existente de una lista de alias."""

        for field_name in field_names:
            if field_name in item:
                return item[field_name]

        return None

    @staticmethod
    def _calculate_percentage(
        *,
        numerator: int,
        denominator: int,
    ) -> float | None:
        """Calcula un porcentaje cuando existe denominador válido."""

        if denominator <= 0:
            return None

        return numerator * 100.0 / denominator

    @staticmethod
    def _loss_denominator(
        *,
        packets_received: int,
        packets_sent: int,
        packets_lost: int,
        role: SessionRole,
    ) -> int:
        """Selecciona la base para estimar pérdida de paquetes."""

        if role is SessionRole.PUBLISHER:
            return packets_received + packets_lost

        if role is SessionRole.READER:
            return packets_sent

        return max(
            packets_received + packets_lost,
            packets_sent,
        )
