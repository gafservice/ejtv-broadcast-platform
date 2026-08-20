"""Renderizador del panel RECENT EVENTS."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models import (
    RecentEventRowData,
    RecentEventsPanelData,
)


class RecentEventsPanelRenderer:
    """Renderiza los eventos operacionales recientes del NOC."""

    _SEVERITY_STYLES = {
        "DEBUG": "dim",
        "INFO": "green",
        "WARNING": "bold yellow",
        "ERROR": "bold red",
        "CRITICAL": "bold red",
    }

    def render(
        self,
        data: RecentEventsPanelData,
    ) -> Panel:
        """Convierte RecentEventsPanelData en un panel Rich."""

        table = Table(
            expand=True,
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 1),
        )

        table.add_column(
            "TIME",
            no_wrap=True,
        )
        table.add_column(
            "SEVERITY",
            no_wrap=True,
        )
        table.add_column(
            "EVENT",
            no_wrap=True,
        )
        table.add_column(
            "TITLE",
        )

        if not data.events:
            table.add_row(
                "-",
                "-",
                "-",
                Text(
                    "No recent events",
                    style="dim",
                ),
            )
        else:
            for event in data.events:
                table.add_row(
                    self._format_time(event),
                    self._format_severity(event),
                    event.event_type,
                    event.title,
                )

        return Panel(
            table,
            title="RECENT EVENTS",
        )

    @staticmethod
    def _format_time(
        event: RecentEventRowData,
    ) -> str:
        """Devuelve una representación compacta de la hora."""

        return event.occurred_at.strftime(
            "%H:%M:%S"
        )

    @classmethod
    def _format_severity(
        cls,
        event: RecentEventRowData,
    ) -> Text:
        """Aplica el estilo visual correspondiente a la severidad."""

        return Text(
            event.severity,
            style=cls._SEVERITY_STYLES.get(
                event.severity,
                "bold dim",
            ),
        )
