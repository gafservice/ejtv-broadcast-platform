"""Renderizador del panel ACTIVE CLIENTS."""

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models import SessionPanelData


class SessionPanelRenderer:
    """Renderiza el resumen de sesiones activas."""

    def render(
        self,
        data: SessionPanelData,
    ) -> Panel:
        """Convierte SessionPanelData en un Panel de Rich."""

        content = Text()

        content.append("Sessions: ")
        content.append(f"{data.total_sessions}\n")

        content.append("Readers: ")
        content.append(f"{data.readers}\n")

        content.append("Publishers: ")
        content.append(f"{data.publishers}\n")

        content.append("Inbound: ")
        content.append(
            f"{self._format_bitrate(data.inbound_bitrate_bps)}\n"
        )

        content.append("Outbound: ")
        content.append(
            f"{self._format_bitrate(data.outbound_bitrate_bps)}\n"
        )

        content.append("Degraded: ")
        content.append(f"{data.degraded_sessions}\n")

        content.append("Critical: ")
        content.append(f"{data.critical_sessions}\n")

        content.append("Quality: ")
        content.append(data.quality)

        return Panel(
            content,
            title="ACTIVE CLIENTS",
            border_style="cyan",
        )

    @staticmethod
    def _format_bitrate(
        bitrate_bps: float | None,
    ) -> str:
        """Convierte bits/s a Mbps."""

        if bitrate_bps is None:
            return "N/A"

        return f"{bitrate_bps / 1_000_000:.2f} Mbps"
