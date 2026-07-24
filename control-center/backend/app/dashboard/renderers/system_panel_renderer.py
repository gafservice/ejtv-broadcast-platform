"""Renderizador del panel SYSTEM."""

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models import SystemPanelData


class SystemPanelRenderer:
    """Renderiza los recursos generales del servidor."""

    def render(self, data: SystemPanelData) -> Panel:
        """Convierte SystemPanelData en un panel legible de Rich."""

        content = Text()

        content.append("CPU: ")
        content.append(f"{data.cpu_usage_percent:.1f}%\n")

        content.append("Cores: ")
        content.append(
            f"{data.physical_cores or 'N/A'} físicos / "
            f"{data.logical_cores} lógicos\n"
        )

        content.append("RAM: ")
        content.append(
            f"{data.memory_usage_percent:.1f}% "
            f"({self._format_bytes(data.memory_used_bytes)} / "
            f"{self._format_bytes(data.memory_total_bytes)})\n"
        )

        content.append("Disco: ")
        content.append(
            f"{data.disk_usage_percent:.1f}% "
            f"({self._format_bytes(data.disk_used_bytes)} / "
            f"{self._format_bytes(data.disk_total_bytes)})\n"
        )

        content.append("Uptime: ")
        content.append(
            self._format_uptime(data.uptime_seconds)
        )

        return Panel(
            content,
            title="SYSTEM",
        )

    @staticmethod
    def _format_bytes(value: int) -> str:
        """Convierte bytes a una unidad legible."""

        units = ("B", "KiB", "MiB", "GiB", "TiB")
        size = float(value)

        for unit in units:
            if size < 1024.0 or unit == units[-1]:
                return f"{size:.1f} {unit}"

            size /= 1024.0

        return f"{size:.1f} TiB"

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Convierte segundos de uptime a días, horas y minutos."""

        total_seconds = int(seconds)

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        return f"{days}d {hours}h {minutes}m"
