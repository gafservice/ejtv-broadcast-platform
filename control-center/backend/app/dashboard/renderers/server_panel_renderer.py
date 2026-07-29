"""Renderizador del panel SERVER."""

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models import ServerPanelData


class ServerPanelRenderer:
    """Renderiza la información general del servidor."""

    def render(self, data: ServerPanelData) -> Panel:
        """Convierte ServerPanelData en un panel legible de Rich."""

        content = Text()

        content.append("Hostname: ")
        content.append(f"{data.hostname}\n")

        content.append("MediaMTX: ")
        content.append(f"{self._format_status(data.mediamtx_online)}\n")

        content.append("API: ")
        content.append(f"{self._format_status(data.api_online)}\n")

        content.append("Snapshot: ")
        content.append(
            data.snapshot_at.isoformat()
            if data.snapshot_at is not None
            else "N/A"
        )
        content.append("\n")

        return Panel(
            content,
            title="SERVER",
        )

    @staticmethod
    def _format_status(online: bool) -> str:
        """Convierte un estado booleano en texto legible."""

        return "ONLINE" if online else "OFFLINE"
