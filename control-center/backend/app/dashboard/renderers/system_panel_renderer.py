"""Renderizador del panel SYSTEM."""

from datetime import timezone

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models import SystemPanelData


class SystemPanelRenderer:
    """Renderiza los recursos generales del servidor."""

    def render(self, data: SystemPanelData) -> Panel:
        """Convierte SystemPanelData en un panel legible de Rich."""

        content = Text()

        content.append("CPU: ")
        self._append_percentage(
            content,
            data.cpu.usage_percent,
        )

        if data.cpu.frequency_mhz is not None:
            content.append(
                f" @ {self._format_frequency(data.cpu.frequency_mhz)}"
            )

        content.append("\n")

        content.append("Cores: ")
        content.append(
            f"{data.cpu.physical_cores or 'N/A'} físicos / "
            f"{data.cpu.logical_cores} lógicos\n"
        )

        if data.cpu.per_core_usage_percent:
            content.append("Por núcleo: ")

            for index, usage in enumerate(
                data.cpu.per_core_usage_percent
            ):
                if index > 0:
                    content.append("  ")

                content.append(
                    f"CPU{index:02d}: "
                )
                self._append_percentage(
                    content,
                    usage,
                )

            content.append("\n")

        content.append("RAM: ")
        self._append_percentage(
            content,
            data.memory.usage_percent,
        )
        content.append(
            f" ({self._format_bytes(data.memory.used_bytes)} / "
            f"{self._format_bytes(data.memory.total_bytes)})\n"
        )

        content.append("Disco: ")
        self._append_percentage(
            content,
            data.disk.usage_percent,
        )
        content.append(
            f" ({self._format_bytes(data.disk.used_bytes)} / "
            f"{self._format_bytes(data.disk.total_bytes)})\n"
        )

        content.append("Red: ")
        content.append(f"{data.network.interface}\n")

        content.append("RX: ")
        content.append(
            self._format_bitrate(data.network.rx_bps)
        )
        content.append(" | TX: ")
        content.append(
            self._format_bitrate(data.network.tx_bps)
        )
        content.append("\n")

        content.append("Errores RX/TX: ")
        content.append(
            f"{data.network.errors_in} / "
            f"{data.network.errors_out}\n"
        )

        content.append("Descartes RX/TX: ")
        content.append(
            f"{data.network.dropped_in} / "
            f"{data.network.dropped_out}\n"
        )

        content.append("Tasa errores RX/TX: ")
        content.append(
            f"{self._format_rate(data.network.errors_in_per_second)} / "
            f"{self._format_rate(data.network.errors_out_per_second)}\n"
        )

        content.append("Tasa drops RX/TX: ")
        content.append(
            f"{self._format_rate(data.network.dropped_in_per_second)} / "
            f"{self._format_rate(data.network.dropped_out_per_second)}\n"
        )

        content.append("Uptime: ")
        content.append(
            f"{self._format_uptime(data.uptime.seconds)}\n"
        )

        content.append("Captured: ")
        content.append(
            self._format_timestamp(data.captured_at)
        )

        return Panel(
            content,
            title="SYSTEM",
        )

    @classmethod
    def _append_percentage(
        cls,
        content: Text,
        value: float,
    ) -> None:
        """Agrega un porcentaje aplicando color según su nivel."""

        content.append(
            f"{value:.1f}%",
            style=cls._percentage_style(value),
        )

    @staticmethod
    def _percentage_style(value: float) -> str:
        """Determina el color asociado a un porcentaje."""

        if value < 50.0:
            return "bold green"

        if value < 80.0:
            return "bold yellow"

        return "bold red"

    @staticmethod
    def _format_frequency(frequency_mhz: float) -> str:
        """Convierte una frecuencia de CPU a MHz o GHz."""

        if frequency_mhz >= 1000.0:
            return f"{frequency_mhz / 1000.0:.2f} GHz"

        return f"{frequency_mhz:.0f} MHz"

    @staticmethod
    def _format_timestamp(value) -> str:
        """Convierte la fecha de captura a formato UTC legible."""

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)

        return value.strftime("%Y-%m-%d %H:%M:%S UTC")

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
    def _format_bitrate(value: float | None) -> str:
        """Convierte una tasa en bps a una unidad legible."""

        if value is None:
            return "N/D"

        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f} Gbps"

        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f} Mbps"

        if value >= 1_000:
            return f"{value / 1_000:.2f} Kbps"

        return f"{value:.0f} bps"

    @staticmethod
    def _format_rate(value: float | None) -> str:
        """Convierte una tasa de eventos a una representación legible."""

        if value is None:
            return "N/D"

        return f"{value:.2f}/s"

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Convierte segundos de uptime a días, horas y minutos."""

        total_seconds = int(seconds)

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        return f"{days}d {hours}h {minutes}m"
