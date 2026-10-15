"""Four-card SIGNAL presentation for INCOMING V2."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_panel import IncomingPanelData
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)


class IncomingSignalCardsRenderer:
    """Present canonical signal evidence without evaluating health."""

    @staticmethod
    def _available(value: object | None) -> str:
        if value is None or value == "":
            return "N/A"
        return str(value)

    @staticmethod
    def _card(title: str, fields: tuple[tuple[str, str], ...]) -> Panel:
        table = Table(
            show_header=False,
            show_edge=False,
            box=None,
            expand=False,
            padding=(0, 1),
        )
        table.add_column("Field", style="bold", no_wrap=True)
        table.add_column("Value", overflow="ellipsis")

        for label, value in fields:
            table.add_row(label, value)

        return Panel(
            table,
            title=title,
            expand=True,
        )

    def render(
        self,
        data: IncomingPanelData | None,
        *,
        selected_path_name: str | None = None,
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

        available = self._available

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

        health_since = IncomingPanelRenderer._format_health_since(
            selected.health_since
        )

        health_duration = (
            IncomingPanelRenderer._format_health_duration(
                health_since=selected.health_since,
                reference_at=data.reference_at,
            )
        )

        if selected.alarm_count == 0:
            alarm_summary = "—"
        elif selected.alarm_severity is None:
            alarm_summary = str(selected.alarm_count)
        else:
            alarm_summary = (
                f"{selected.alarm_count} {selected.alarm_severity}"
            )

        identification = self._card(
            "IDENTIFICACIÓN",
            (
                ("Path", selected.path_name),
                ("Source", available(selected.source)),
                ("Protocol", available(selected.protocol)),
                ("Remote", available(selected.remote_address)),
            ),
        )

        reception = self._card(
            "RECEPCIÓN",
            (
                ("Status", available(selected.status)),
                ("Receive", bitrate),
                ("Since", "N/A"),
                ("Duration", "N/A"),
            ),
        )

        health_card = self._card(
            "HEALTH",
            (
                ("Status", health),
                ("Reason", available(selected.health_reason)),
                ("Since", health_since),
                ("Duration", health_duration),
            ),
        )

        alarms = self._card(
            "ALARMAS",
            (
                ("Count", str(selected.alarm_count)),
                ("Severity", available(selected.alarm_severity)),
                ("Summary", alarm_summary),
            ),
        )

        content = Table.grid(
            padding=(0, 1),
            expand=True,
        )
        content.add_column(ratio=1)
        content.add_column(ratio=1)
        content.add_row(identification, reception)
        content.add_row(health_card, alarms)

        return Panel(
            content,
            title="SIGNAL DETAIL",
        )
