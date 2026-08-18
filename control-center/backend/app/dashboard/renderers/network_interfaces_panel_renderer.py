"""Renderizador del panel NETWORK INTERFACES."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models import (
    NetworkInterfaceRowData,
    NetworkInterfacesPanelData,
)


class NetworkInterfacesPanelRenderer:
    """Renderiza el estado y tráfico de todas las interfaces."""

    def render(
        self,
        data: NetworkInterfacesPanelData,
    ) -> Panel:
        """Convierte la telemetría Multi-Interface en un panel Rich."""

        table = Table(
            expand=True,
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 1),
        )

        table.add_column(
            "INTERFACE",
            no_wrap=True,
        )
        table.add_column(
            "TYPE",
            no_wrap=True,
        )
        table.add_column(
            "STATE",
            no_wrap=True,
        )
        table.add_column(
            "LINK",
            no_wrap=True,
        )
        table.add_column(
            "RX",
            justify="right",
            no_wrap=True,
        )
        table.add_column(
            "TX",
            justify="right",
            no_wrap=True,
        )
        table.add_column(
            "DROP RX",
            justify="right",
            no_wrap=True,
        )

        for interface in data.interfaces:
            table.add_row(
                interface.interface,
                self._format_type(interface),
                self._format_state(interface),
                self._format_link(interface),
                self._format_bitrate(
                    interface.rx_bps
                ),
                self._format_bitrate(
                    interface.tx_bps
                ),
                self._format_rate(
                    interface.dropped_in_per_second
                ),
            )

        return Panel(
            table,
            title="NETWORK INTERFACES",
        )

    @staticmethod
    def _format_type(
        interface: NetworkInterfaceRowData,
    ) -> str:
        """Devuelve una etiqueta compacta para el tipo."""

        labels = {
            "ETHERNET": "ETH",
            "WIFI": "WIFI",
            "LOOPBACK": "LOOP",
            "BRIDGE": "BRIDGE",
            "BOND": "BOND",
            "VLAN": "VLAN",
            "TUNNEL": "TUNNEL",
            "VIRTUAL": "VIRTUAL",
            "UNKNOWN": "UNKNOWN",
        }

        return labels.get(
            interface.interface_type,
            interface.interface_type,
        )

    @staticmethod
    def _format_state(
        interface: NetworkInterfaceRowData,
    ) -> Text:
        """Representa estado administrativo y carrier."""

        if not interface.is_up:
            return Text(
                "DOWN",
                style="bold red",
            )

        if interface.carrier is False:
            return Text(
                "NO CARRIER",
                style="bold yellow",
            )

        return Text(
            "UP",
            style="bold green",
        )

    @staticmethod
    def _format_link(
        interface: NetworkInterfaceRowData,
    ) -> str:
        """Representa la velocidad negociada del enlace."""

        speed = interface.link_speed_mbps

        if speed is None:
            return "N/D"

        if speed >= 1000:
            return f"{speed / 1000.0:g} Gbps"

        return f"{speed} Mbps"

    @staticmethod
    def _format_bitrate(
        value: float | None,
    ) -> str:
        """Convierte bits por segundo a una unidad legible."""

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
    def _format_rate(
        value: float | None,
    ) -> str:
        """Convierte una tasa de eventos a eventos por segundo."""

        if value is None:
            return "N/D"

        return f"{value:.2f}/s"
