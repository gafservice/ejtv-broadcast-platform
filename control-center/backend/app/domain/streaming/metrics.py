"""Modelos del dominio para métricas multimedia derivadas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .models import MediaPathStatus


class MeasurementQuality(StrEnum):
    """Calidad y disponibilidad de una medición calculada."""

    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    INVALID = "INVALID"
    STALE = "STALE"


@dataclass(frozen=True, slots=True)
class StreamingPathMeasurement:
    """Medición derivada para un path multimedia."""

    name: str
    status: MediaPathStatus
    previous_status: MediaPathStatus | None

    reader_count: int
    reader_delta: int | None

    inbound_delta_bytes: int | None
    outbound_delta_bytes: int | None

    inbound_bitrate_bps: float | None
    outbound_bitrate_bps: float | None

    state_changed: bool
    quality: MeasurementQuality

    def __post_init__(self) -> None:
        """Valida la coherencia básica de la medición."""

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("El nombre del path debe contener texto válido.")

        object.__setattr__(self, "name", self.name.strip())

        if self.reader_count < 0:
            raise ValueError(
                "La cantidad actual de lectores no puede ser negativa."
            )

        for field_name, value in (
            ("inbound_delta_bytes", self.inbound_delta_bytes),
            ("outbound_delta_bytes", self.outbound_delta_bytes),
        ):
            if value is not None and value < 0:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser negativo."
                )

        for field_name, value in (
            ("inbound_bitrate_bps", self.inbound_bitrate_bps),
            ("outbound_bitrate_bps", self.outbound_bitrate_bps),
        ):
            if value is not None and value < 0:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser negativo."
                )

        if self.quality is MeasurementQuality.AVAILABLE:
            required_values = (
                self.reader_delta,
                self.inbound_delta_bytes,
                self.outbound_delta_bytes,
                self.inbound_bitrate_bps,
                self.outbound_bitrate_bps,
            )

            if any(value is None for value in required_values):
                raise ValueError(
                    "Una medición AVAILABLE debe contener todos "
                    "los valores derivados."
                )

    @property
    def inbound_bitrate_mbps(self) -> float | None:
        """Retorna el bitrate de entrada expresado en Mbps."""

        if self.inbound_bitrate_bps is None:
            return None

        return self.inbound_bitrate_bps / 1_000_000

    @property
    def outbound_bitrate_mbps(self) -> float | None:
        """Retorna el bitrate de salida expresado en Mbps."""

        if self.outbound_bitrate_bps is None:
            return None

        return self.outbound_bitrate_bps / 1_000_000

    @property
    def readers_connected(self) -> int:
        """Cantidad de lectores conectados durante el intervalo."""

        if self.reader_delta is None:
            return 0

        return max(self.reader_delta, 0)

    @property
    def readers_disconnected(self) -> int:
        """Cantidad de lectores desconectados durante el intervalo."""

        if self.reader_delta is None:
            return 0

        return abs(min(self.reader_delta, 0))


@dataclass(frozen=True, slots=True)
class StreamingMeasurement:
    """Medición derivada entre dos snapshots multimedia."""

    captured_at: datetime
    previous_captured_at: datetime | None
    interval_seconds: float | None

    paths: tuple[StreamingPathMeasurement, ...]

    total_inbound_bitrate_bps: float | None
    total_outbound_bitrate_bps: float | None

    quality: MeasurementQuality

    def __post_init__(self) -> None:
        """Valida la coherencia temporal y numérica."""

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at debe incluir información de zona horaria."
            )

        if (
            self.previous_captured_at is not None
            and self.previous_captured_at.tzinfo is None
        ):
            raise ValueError(
                "previous_captured_at debe incluir zona horaria."
            )

        if self.interval_seconds is not None and self.interval_seconds <= 0:
            raise ValueError(
                "El intervalo de medición debe ser mayor que cero."
            )

        for field_name, value in (
            (
                "total_inbound_bitrate_bps",
                self.total_inbound_bitrate_bps,
            ),
            (
                "total_outbound_bitrate_bps",
                self.total_outbound_bitrate_bps,
            ),
        ):
            if value is not None and value < 0:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser negativo."
                )

        if self.quality is MeasurementQuality.AVAILABLE:
            if self.previous_captured_at is None:
                raise ValueError(
                    "Una medición AVAILABLE requiere un snapshot anterior."
                )

            if self.interval_seconds is None:
                raise ValueError(
                    "Una medición AVAILABLE requiere un intervalo."
                )

            if self.total_inbound_bitrate_bps is None:
                raise ValueError(
                    "Una medición AVAILABLE requiere bitrate de entrada."
                )

            if self.total_outbound_bitrate_bps is None:
                raise ValueError(
                    "Una medición AVAILABLE requiere bitrate de salida."
                )

    @property
    def path_count(self) -> int:
        """Cantidad de paths incluidos en la medición."""

        return len(self.paths)

    @property
    def valid_path_count(self) -> int:
        """Cantidad de paths con mediciones disponibles."""

        return sum(
            path.quality is MeasurementQuality.AVAILABLE
            for path in self.paths
        )

    @property
    def state_change_count(self) -> int:
        """Cantidad de paths que cambiaron de estado."""

        return sum(path.state_changed for path in self.paths)

    @property
    def total_reader_count(self) -> int:
        """Cantidad actual de lectores entre todos los paths."""

        return sum(path.reader_count for path in self.paths)

    @property
    def total_inbound_bitrate_mbps(self) -> float | None:
        """Bitrate total de entrada expresado en Mbps."""

        if self.total_inbound_bitrate_bps is None:
            return None

        return self.total_inbound_bitrate_bps / 1_000_000

    @property
    def total_outbound_bitrate_mbps(self) -> float | None:
        """Bitrate total de salida expresado en Mbps."""

        if self.total_outbound_bitrate_bps is None:
            return None

        return self.total_outbound_bitrate_bps / 1_000_000

    def get_path(
        self,
        name: str,
    ) -> StreamingPathMeasurement | None:
        """Busca una medición por nombre de path."""

        return next(
            (path for path in self.paths if path.name == name),
            None,
        )
