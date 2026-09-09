"""Modelo de presentación para PLATFORM HEALTH."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PlatformHealthPanelData:
    """Resumen agregado de salud preparado para el dashboard."""

    status: str
    worst_status: str
    healthy_count: int
    degraded_count: int
    critical_count: int
    unknown_count: int
    evidence_coverage: float | None
    affected_fraction: float | None
    service_count: int
    captured_at: datetime

    def __post_init__(self) -> None:
        """Valida las invariantes básicas del modelo de presentación."""

        for field_name in (
            "healthy_count",
            "degraded_count",
            "critical_count",
            "unknown_count",
            "service_count",
        ):
            value = getattr(self, field_name)

            if value < 0:
                raise ValueError(
                    f"El campo '{field_name}' no puede ser negativo."
                )

        for field_name in (
            "evidence_coverage",
            "affected_fraction",
        ):
            value = getattr(self, field_name)

            if value is None:
                continue

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"El campo '{field_name}' debe estar entre 0 y 1."
                )

        if (
            self.captured_at.tzinfo is None
            or self.captured_at.utcoffset() is None
        ):
            raise ValueError(
                "El campo 'captured_at' debe incluir zona horaria."
            )
