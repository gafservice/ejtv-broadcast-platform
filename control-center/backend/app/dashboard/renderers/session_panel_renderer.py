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

        for protocol, count in data.protocol_counts:
            if protocol == "UNKNOWN":
                continue

            content.append(f"{protocol}: ")
            content.append(f"{count}\n")

        content.append("TOTAL: ")
        content.append(f"{data.total_sessions}\n")

        average_bitrate_bps: float | None = None

        if (
            data.total_sessions > 0
            and data.outbound_bitrate_bps is not None
        ):
            average_bitrate_bps = (
                data.outbound_bitrate_bps
                / data.total_sessions
            )

        content.append("Total traffic: ")
        content.append(
            f"{self._format_bitrate(data.outbound_bitrate_bps)}\n"
        )

        content.append("Avg/client: ")
        content.append(
            f"{self._format_bitrate(average_bitrate_bps)}\n"
        )

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