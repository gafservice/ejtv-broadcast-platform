"""Renderizador del panel PLATFORM HEALTH."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models import PlatformHealthPanelData


class PlatformHealthRenderer:
    """Renderiza el resumen agregado de salud de la plataforma."""

    _STATUS_STYLES = {
        "HEALTHY": "bold green",
        "DEGRADED": "bold yellow",
        "CRITICAL": "bold red",
        "UNKNOWN": "bold dim",
    }

    _BORDER_STYLES = {
        "HEALTHY": "green",
        "DEGRADED": "yellow",
        "CRITICAL": "red",
        "UNKNOWN": "blue",
    }

    def render(
        self,
        data: PlatformHealthPanelData | None,
    ) -> Panel:
        """Convierte PlatformHealthPanelData en un panel Rich."""

        if data is None:
            return self._render_unavailable()

        content = Text()

        content.append("Status: ")
        content.append(
            data.status,
            style=self._status_style(data.status),
        )
        content.append("\n")

        content.append("Worst: ")
        content.append(
            data.worst_status,
            style=self._status_style(data.worst_status),
        )
        content.append("\n")

        content.append(f"Services: {data.service_count}\n")
        content.append(
            "Coverage: "
            f"{self._format_fraction(data.evidence_coverage)}\n"
        )
        content.append(
            "Affected: "
            f"{self._format_fraction(data.affected_fraction)}\n"
        )
        content.append(
            f"H:{data.healthy_count} "
            f"D:{data.degraded_count} "
            f"C:{data.critical_count} "
            f"U:{data.unknown_count}"
        )

        return Panel(
            content,
            title="PLATFORM HEALTH",
            border_style=self._border_style(data.status),
        )

    def _render_unavailable(self) -> Panel:
        """Renderiza ausencia de información de Platform Health."""

        content = Text()
        content.append("Status: ")
        content.append(
            "UNKNOWN",
            style=self._status_style("UNKNOWN"),
        )
        content.append("\n")
        content.append("Worst: UNKNOWN\n")
        content.append("Services: 0\n")
        content.append("Coverage: N/A\n")
        content.append("Affected: N/A\n")
        content.append("H:0 D:0 C:0 U:0")

        return Panel(
            content,
            title="PLATFORM HEALTH",
            border_style=self._border_style("UNKNOWN"),
        )

    @staticmethod
    def _format_fraction(value: float | None) -> str:
        """Formatea una fracción ya calculada como porcentaje."""

        if value is None:
            return "N/A"

        return f"{value * 100:.0f}%"

    @classmethod
    def _status_style(cls, status: str) -> str:
        """Obtiene el estilo visual del estado recibido."""

        return cls._STATUS_STYLES.get(
            status,
            "bold dim",
        )

    @classmethod
    def _border_style(cls, status: str) -> str:
        """Obtiene el estilo del borde para el estado recibido."""

        return cls._BORDER_STYLES.get(
            status,
            "blue",
        )
