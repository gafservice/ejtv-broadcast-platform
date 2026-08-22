"""Renderizador del panel ACTIVE ALARMS."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models import (
    ActiveAlarmRowData,
    ActiveAlarmsPanelData,
)


class ActiveAlarmsPanelRenderer:
    """Renderiza las alarmas operacionales que requieren atención."""

    _SEVERITY_STYLES = {
        "INFO": "green",
        "WARNING": "bold yellow",
        "MINOR": "yellow",
        "MAJOR": "bold yellow",
        "CRITICAL": "bold red",
    }

    _STATE_STYLES = {
        "ACTIVE": "bold red",
        "ACKNOWLEDGED": "bold yellow",
    }

    def render(
        self,
        data: ActiveAlarmsPanelData,
    ) -> Panel:
        """Convierte ActiveAlarmsPanelData en un panel Rich."""

        if not isinstance(
            data,
            ActiveAlarmsPanelData,
        ):
            raise TypeError(
                "data must be an ActiveAlarmsPanelData"
            )

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
            "STATE",
            no_wrap=True,
        )

        table.add_column(
            "ALARM",
            no_wrap=True,
        )

        table.add_column(
            "MESSAGE",
        )

        if not data.alarms:
            table.add_row(
                "-",
                "-",
                "-",
                "-",
                Text(
                    "No active alarms",
                    style="dim",
                ),
            )
        else:
            for alarm in data.alarms:
                table.add_row(
                    self._format_time(
                        alarm
                    ),
                    self._format_severity(
                        alarm
                    ),
                    self._format_state(
                        alarm
                    ),
                    alarm.alarm_type,
                    alarm.message,
                )

        return Panel(
            table,
            title="ACTIVE ALARMS",
        )

    @staticmethod
    def _format_time(
        alarm: ActiveAlarmRowData,
    ) -> str:
        """Devuelve una representación compacta de la hora."""

        return alarm.opened_at.strftime(
            "%H:%M:%S"
        )

    @classmethod
    def _format_severity(
        cls,
        alarm: ActiveAlarmRowData,
    ) -> Text:
        """Aplica estilo visual según severidad."""

        return Text(
            alarm.severity,
            style=cls._SEVERITY_STYLES.get(
                alarm.severity,
                "bold dim",
            ),
        )

    @classmethod
    def _format_state(
        cls,
        alarm: ActiveAlarmRowData,
    ) -> Text:
        """Aplica estilo visual según estado operacional."""

        return Text(
            alarm.state,
            style=cls._STATE_STYLES.get(
                alarm.state,
                "bold dim",
            ),
        )
