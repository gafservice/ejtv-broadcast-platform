"""Renderizador del panel de salud del streaming."""

from rich.panel import Panel
from rich.text import Text

from app.domain.streaming import HealthStatus, StreamingHealth


class StreamingHealthRenderer:
    """Renderiza el estado general de salud del streaming."""

    _STATUS_STYLES = {
        HealthStatus.HEALTHY: "bold green",
        HealthStatus.DEGRADED: "bold yellow",
        HealthStatus.CRITICAL: "bold red",
        HealthStatus.UNKNOWN: "bold dim",
    }

    _BORDER_STYLES = {
        HealthStatus.HEALTHY: "green",
        HealthStatus.DEGRADED: "yellow",
        HealthStatus.CRITICAL: "red",
        HealthStatus.UNKNOWN: "blue",
    }

    def render(
        self,
        health: StreamingHealth | None,
    ) -> Panel:
        """Convierte StreamingHealth en un panel legible de Rich."""

        if health is None:
            return self._render_unavailable()

        content = Text()

        content.append("Status: ")
        content.append(
            health.status.value,
            style=self._status_style(health.status),
        )
        content.append("\n")

        content.append("Paths: ")
        content.append(f"{health.path_count}\n")

        content.append("Connections: ")
        content.append(f"{health.connection_count}\n")

        content.append("Captured: ")
        content.append(
            health.captured_at.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        )
        content.append("\n")

        content.append("Summary: ")
        content.append(
            self._format_message(health.message)
        )

        return Panel(
            content,
            title="STREAM HEALTH",
            border_style=self._border_style(
                health.status
            ),
        )

    def _render_unavailable(self) -> Panel:
        """Construye el panel cuando no existe información de salud."""

        content = Text()

        content.append("Status: ")
        content.append(
            HealthStatus.UNKNOWN.value,
            style=self._status_style(
                HealthStatus.UNKNOWN
            ),
        )
        content.append("\n")

        content.append("Paths: 0\n")
        content.append("Connections: 0\n")
        content.append("Captured: N/A\n")
        content.append(
            "Summary: No health data available."
        )

        return Panel(
            content,
            title="STREAM HEALTH",
            border_style=self._border_style(
                HealthStatus.UNKNOWN
            ),
        )

    @staticmethod
    def _format_message(
        message: str,
        *,
        max_length: int = 38,
    ) -> str:
        """Acorta mensajes extensos sin cortar palabras."""

        normalized = " ".join(message.split())

        if len(normalized) <= max_length:
            return normalized

        shortened = normalized[
            : max_length - 1
        ].rsplit(" ", 1)[0]

        if not shortened:
            shortened = normalized[
                : max_length - 1
            ]

        return f"{shortened}…"

    def _status_style(
        self,
        status: HealthStatus,
    ) -> str:
        """Obtiene el estilo correspondiente al estado."""

        return self._STATUS_STYLES.get(
            status,
            "bold dim",
        )

    def _border_style(
        self,
        status: HealthStatus,
    ) -> str:
        """Obtiene el estilo del borde correspondiente."""

        return self._BORDER_STYLES.get(
            status,
            "blue",
        )