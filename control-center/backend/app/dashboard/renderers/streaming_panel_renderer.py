"""Renderizador del panel STREAMING."""

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models import StreamingPanelData


class StreamingPanelRenderer:
    """Renderiza el resumen general del streaming."""

    def render(self, data: StreamingPanelData) -> Panel:
        """Convierte StreamingPanelData en un panel legible de Rich."""

        content = Text()

        content.append("Paths: ")
        content.append(f"{data.active_paths}\n")

        content.append("Readers: ")
        content.append(f"{data.readers}\n")

        content.append("Inbound: ")
        content.append(
            f"{self._format_bitrate(data.inbound_bitrate_bps)}\n"
        )

        content.append("Outbound: ")
        content.append(
            f"{self._format_bitrate(data.outbound_bitrate_bps)}\n"
        )

        content.append("Status: ")
        content.append(data.quality)

        return Panel(
            content,
            title="STREAMING",
        )

    @staticmethod
    def _format_bitrate(bitrate_bps: float | None) -> str:
        """Convierte bits por segundo a megabits por segundo."""

        if bitrate_bps is None:
            return "N/A"

        bitrate_mbps = bitrate_bps / 1_000_000

        return f"{bitrate_mbps:.2f} Mbps"