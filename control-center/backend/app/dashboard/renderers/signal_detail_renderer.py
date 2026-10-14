"""Contextual presentation of one selected INCOMING signal."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models.incoming_panel import IncomingPanelData
from app.dashboard.renderers.incoming_panel_renderer import IncomingPanelRenderer


class SignalDetailRenderer:
    """Render existing presentation evidence without evaluating health."""

    def render(
        self,
        data: IncomingPanelData | None,
        selected_path_name: str | None = None,
        compact: bool = False,
    ) -> Panel:
        selected = None

        if data is not None and selected_path_name is not None:
            selected = next(
                (
                    row
                    for row in data.rows
                    if row.path_name == selected_path_name
                ),
                None,
            )

        if selected is None:
            return Panel(
                "No incoming signal selected.",
                title="SIGNAL DETAIL",
            )

        def available(value: object | None) -> str:
            if value is None or value == "":
                return "N/A"
            return str(value)

        health = (
            selected.health_status.value
            if selected.health_status is not None
            else "N/A"
        )

        bitrate = (
            f"{selected.bitrate_receive_mbps:.2f} Mbps"
            if selected.bitrate_receive_mbps is not None
            else "N/A"
        )

        if selected.alarm_count == 0:
            alarm_summary = "—"
        elif selected.alarm_severity is None:
            alarm_summary = str(selected.alarm_count)
        else:
            alarm_summary = (
                f"{selected.alarm_count} {selected.alarm_severity}"
            )

        if compact:
            compact_table = Table(
                show_header=False,
                expand=False,
                box=None,
                padding=(0, 1),
            )
            compact_table.add_column(
                "Field", style="bold", no_wrap=True
            )
            compact_table.add_column("Value")

            compact_table.add_row(
                "Signal", selected.path_name
            )
            compact_table.add_row(
                "Health", health
            )
            compact_table.add_row(
                "Alarms", alarm_summary
            )
            compact_table.add_row(
                "Status", available(selected.status)
            )
            compact_table.add_row(
                "Receive", bitrate
            )
            compact_table.add_row(
                "Protocol", available(selected.protocol)
            )
            compact_table.add_row(
                "Source",
                Text(
                    available(selected.source),
                    overflow="ellipsis",
                    no_wrap=True,
                ),
            )
            compact_table.add_row(
                "Remote",
                Text(
                    available(selected.remote_address),
                    overflow="ellipsis",
                    no_wrap=True,
                ),
            )
            compact_table.add_row(
                "More", "Expand terminal for details"
            )

            return Panel(
                compact_table,
                title="SIGNAL DETAIL",
            )

        table = Table(
            show_header=False,
            expand=False,
            box=None,
        )

        table.add_column("Field", style="bold", no_wrap=True)
        table.add_column("Value")

        table.add_row("Identification", "")
        table.add_row("Path", selected.path_name)
        table.add_row("Source", available(selected.source))

        table.add_row("Transport", "")
        table.add_row("Protocol", available(selected.protocol))
        table.add_row("Remote", available(selected.remote_address))

        table.add_row("Reception", "")
        table.add_row("Status", available(selected.status))
        table.add_row("Receive", bitrate)

        table.add_row("Health", "")
        table.add_row("Health Status", health)
        table.add_row("Reason", available(selected.health_reason))
        table.add_row(
            "Since",
            IncomingPanelRenderer._format_health_since(
                selected.health_since
            ),
        )

        table.add_row(
            "Duration",
            IncomingPanelRenderer._format_health_duration(
                health_since=selected.health_since,
                reference_at=data.reference_at,
            ),
        )

        table.add_row("Alarms", "")
        table.add_row("Count", str(selected.alarm_count))
        table.add_row(
            "Severity",
            available(selected.alarm_severity),
        )
        table.add_row("Summary", alarm_summary)

        return Panel(
            table,
            title="SIGNAL DETAIL",
        )
