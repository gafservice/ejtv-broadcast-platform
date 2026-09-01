"""Modelos de presentación para el panel CONNECTED CLIENTS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ActiveConnectionRow:
    """Información preparada para una conexión activa."""

    session_id: str
    remote_address: str
    country: str
    country_code: str | None
    asn: int | None
    provider: str

    protocol: str
    path: str
    role: str

    bitrate_bps: float | None
    uptime_seconds: float

    username: str | None = None

    def __post_init__(self) -> None:

        """Valida los valores utilizados por una fila."""

        text_values = (
            ("session_id", self.session_id),
            ("remote_address", self.remote_address),
            ("country", self.country),
            ("provider", self.provider),
            ("protocol", self.protocol),
            ("path", self.path),
            ("role", self.role),
        )

        for field_name, value in text_values:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} debe contener texto válido."
                )

        if self.country_code is not None:
            normalized_country_code = self.country_code.strip().upper()

            if (
                len(normalized_country_code) != 2
                or not normalized_country_code.isalpha()
            ):
                raise ValueError(
                    "country_code debe ser un código ISO de dos letras."
                )

        if self.bitrate_bps is not None and self.bitrate_bps < 0:
            raise ValueError(
                "bitrate_bps no puede ser negativo."
            )

        if self.uptime_seconds < 0:
            raise ValueError(
                "uptime_seconds no puede ser negativo."
            )

        if self.username is not None and not self.username.strip():
            raise ValueError(
                "username no puede estar vacío cuando se proporciona."
            )

@dataclass(frozen=True, slots=True)
class ActiveConnectionsPanelData:
    """Datos completos requeridos por CONNECTED CLIENTS."""

    captured_at: datetime
    connections: tuple[ActiveConnectionRow, ...]
    total_items: int | None = None

    def __post_init__(self) -> None:
        if self.total_items is not None:
            if (
                isinstance(self.total_items, bool)
                or not isinstance(self.total_items, int)
            ):
                raise TypeError(
                    "total_items must be an int or None"
                )

            if self.total_items < 0:
                raise ValueError(
                    "total_items must be greater than or equal to zero"
                )

        """Valida invariantes generales del panel."""

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at debe contener información de zona horaria."
            )

        session_ids = [
            connection.session_id
            for connection in self.connections
        ]

        if len(session_ids) != len(set(session_ids)):
            raise ValueError(
                "No se permiten session_id duplicados."
            )

    @property
    def connection_count(self) -> int:
        """Cantidad de conexiones presentes en el panel."""

        return len(self.connections)

    @classmethod
    def empty(
        cls,
        *,
        captured_at: datetime,
    ) -> "ActiveConnectionsPanelData":
        """Construye un panel sin conexiones activas."""

        return cls(
            captured_at=captured_at,
            connections=(),
        )
