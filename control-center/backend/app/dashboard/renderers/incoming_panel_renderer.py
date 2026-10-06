"""Renderer for the INCOMING terminal dashboard view."""

from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)


class IncomingPanelRenderer:
    """Render canonical incoming-path presentation data."""

    def render(
        self,
        data: IncomingPanelData | None,
    ) -> Panel:
        """Render the incoming signals panel."""

        if data is None:
            return Panel(
                "Incoming data unavailable.",
                title="INCOMING SIGNALS",
            )

        if not data.rows:
            return Panel(
                "No incoming signals.",
                title="INCOMING SIGNALS",
            )

        table = Table(
            box=None,
            expand=True,
        )

        table.add_column("Path")
        table.add_column("Source")
        table.add_column("Protocol")
        table.add_column("Remote")
        table.add_column("Receive")
        table.add_column("Status")
        table.add_column("Health")

        for row in data.rows:
            table.add_row(
                row.path_name,
                row.source,
                self._format_optional(row.protocol),
                self._format_optional(row.remote_address),
                self._format_bitrate(
                    row.bitrate_receive_mbps
                ),
                row.status,
                self._format_health(row),
            )

        return Panel(
            table,
            title="INCOMING SIGNALS",
        )

    @staticmethod
    def _format_optional(value: str | None) -> str:
        """Present optional text without inferring evidence."""

        return value if value is not None else "N/A"

    @staticmethod
    def _format_bitrate(value: float | None) -> str:
        """Present an already-normalized Mbps value."""

        if value is None:
            return "N/A"

        return f"{value:.2f} Mbps"

    @staticmethod
    def _format_health(row: IncomingRowData) -> str:
        """Present canonical Health without recomputation."""

        if row.health_status is None:
            return "N/A"

        return row.health_status.value
