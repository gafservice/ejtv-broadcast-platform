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
        *,
        selected_path_name: str | None = None,
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
        table.add_column("Origin")
        table.add_column("Receive")
        table.add_column("Status")
        table.add_column("Health")
        table.add_column("Alarms")
        table.add_column("Since")
        table.add_column("Duration")
        table.add_column("Reason")

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
                self._format_alarm_indicator(row),
                self._format_health_since(row.health_since),
                self._format_health_duration(
                    health_since=row.health_since,
                    reference_at=data.reference_at,
                ),
                self._format_optional(row.health_reason),
                style=(
                    "reverse"
                    if row.path_name == selected_path_name
                    and selected_path_name is not None
                    else None
                ),
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


    @staticmethod
    def _format_alarm_indicator(row: IncomingRowData) -> str:
        """Present an already-projected canonical alarm indicator."""

        if row.alarm_count == 0:
            return "—"

        if row.alarm_severity is None:
            return str(row.alarm_count)

        return f"{row.alarm_count} {row.alarm_severity}"

    @staticmethod
    def _format_health_since(value) -> str:
        """Present the canonical state-start timestamp."""

        if value is None:
            return "N/A"

        return value.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _format_health_duration(
        *,
        health_since,
        reference_at,
    ) -> str:
        """Derive duration from canonical state-start and snapshot time."""

        if health_since is None or reference_at is None:
            return "N/A"

        duration_seconds = (
            reference_at - health_since
        ).total_seconds()

        if duration_seconds < 0:
            return "N/A"

        total_seconds = int(duration_seconds)

        days, remainder = divmod(
            total_seconds,
            86_400,
        )
        hours, remainder = divmod(
            remainder,
            3_600,
        )
        minutes, seconds = divmod(
            remainder,
            60,
        )

        if days > 0:
            return (
                f"{days}d "
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )
