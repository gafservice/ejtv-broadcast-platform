"""Renderizador del panel CONNECTED CLIENTS."""

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models import (
    ActiveConnectionRow,
    ActiveConnectionsPanelData,
)


class ActiveConnectionsPanelRenderer:
    """Renderiza el detalle de las conexiones activas."""

    def render(
        self,
        data: ActiveConnectionsPanelData,
    ) -> Panel:
        """Convierte ActiveConnectionsPanelData en un panel de Rich."""

        if not data.connections:
            return Panel(
                Text(
                    "No hay clientes conectados.",
                    justify="center",
                ),
                title="CONNECTED CLIENTS",
                border_style="cyan",
            )

        table = Table(
            box=box.SIMPLE_HEAVY,
            expand=True,
            show_header=True,
            header_style="bold",
            pad_edge=False,
        )

        table.add_column(
            "CLIENT",
            overflow="fold",
            ratio=2,
        )
        table.add_column(
            "REMOTE ADDRESS",
            no_wrap=True,
            ratio=3,
        )
        table.add_column(
            "COUNTRY",
            overflow="fold",
            ratio=2,
        )
        table.add_column(
            "ASN",
            no_wrap=True,
            ratio=1,
        )
        table.add_column(
            "PROVIDER",
            overflow="fold",
            ratio=3,
        )
        table.add_column(
            "PROTOCOL",
            no_wrap=True,
            ratio=1,
        )
        table.add_column(
            "BITRATE",
            justify="right",
            no_wrap=True,
            ratio=2,
        )
        table.add_column(
            "ROLE",
            no_wrap=True,
            ratio=1,
        )
        table.add_column(
            "UPTIME",
            justify="right",
            no_wrap=True,
            ratio=2,
        )

        for connection in data.connections:
            table.add_row(
                self._format_client(connection),
                self._format_text(
                    connection.remote_address,
                    fallback="UNKNOWN",
                ),
                self._format_country(
                    connection.country_code,
                ),
                self._format_asn(
                    connection.asn,
                ),
                self._format_text(
                    connection.provider,
                    fallback="UNKNOWN",
                ),
                self._format_text(
                    connection.protocol,
                    fallback="UNKNOWN",
                ),
                self._format_bitrate(
                    connection.bitrate_bps,
                ),
                self._format_text(
                    connection.role,
                    fallback="UNKNOWN",
                ),
                self._format_uptime(
                    connection.uptime_seconds,
                ),
            )

        return Panel(
            table,
            title=(
                "CONNECTED CLIENTS "
                f"[{len(data.connections)}]"
            ),
            border_style="cyan",
        )

    @staticmethod
    def _format_country(
        country_code: str | None,
    ) -> str:
        """Convierte un código ISO de dos letras en bandera y código."""

        if country_code is None:
            return "🌍 --"

        code = country_code.strip().upper()

        if len(code) != 2 or not code.isalpha():
            return "🌍 --"

        flag = "".join(
            chr(0x1F1E6 + ord(letter) - ord("A"))
            for letter in code
        )

        return f"{flag} {code}"

    @classmethod
    def _format_client(
        cls,
        connection: ActiveConnectionRow,
    ) -> str:
        """Obtiene la mejor identificación disponible del cliente."""

        if connection.username is not None:
            username = connection.username.strip()

            if username:
                return username

        path = connection.path.strip()

        return path if path else "UNKNOWN"

    @staticmethod
    def _format_text(
        value: str | None,
        *,
        fallback: str,
    ) -> str:
        """Normaliza texto vacío o ausente."""

        if value is None:
            return fallback

        normalized = value.strip()

        return normalized if normalized else fallback

    @staticmethod
    def _format_asn(
        asn: int | None,
    ) -> str:
        """Convierte el número ASN en una etiqueta legible."""

        if asn is None or asn < 0:
            return "N/A"

        return f"AS{asn}"

    @staticmethod
    def _format_bitrate(
        bitrate_bps: float | None,
    ) -> str:
        """Convierte bits por segundo a una unidad legible."""

        if bitrate_bps is None or bitrate_bps < 0:
            return "N/A"

        if bitrate_bps >= 1_000_000_000:
            return (
                f"{bitrate_bps / 1_000_000_000:.2f} Gbps"
            )

        if bitrate_bps >= 1_000_000:
            return (
                f"{bitrate_bps / 1_000_000:.2f} Mbps"
            )

        if bitrate_bps >= 1_000:
            return f"{bitrate_bps / 1_000:.2f} kbps"

        return f"{bitrate_bps:.0f} bps"

    @staticmethod
    def _format_uptime(
        uptime_seconds: float | None,
    ) -> str:
        """Convierte una duración en segundos a una etiqueta legible."""

        if uptime_seconds is None or uptime_seconds < 0:
            return "N/A"

        total_seconds = int(uptime_seconds)

        days, remainder = divmod(total_seconds, 86_400)
        hours, remainder = divmod(remainder, 3_600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return (
                f"{days}d "
                f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            )

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
