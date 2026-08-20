"""Renderizador del panel NODE HEALTH."""

from __future__ import annotations

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models import NodeHealthPanelData


class NodeHealthPanelRenderer:
    """Renderiza la salud operacional integral del Node."""

    _STATUS_STYLES = {
        "HEALTHY": "bold green",
        "WARNING": "bold yellow",
        "DEGRADED": "bold yellow",
        "CRITICAL": "bold red",
        "UNKNOWN": "bold dim",
    }

    _BORDER_STYLES = {
        "HEALTHY": "green",
        "WARNING": "yellow",
        "DEGRADED": "yellow",
        "CRITICAL": "red",
        "UNKNOWN": "blue",
    }

    def render(
        self,
        data: NodeHealthPanelData | None,
    ) -> Panel:
        """Convierte NodeHealthPanelData en un panel Rich."""

        if data is None:
            return self._render_unavailable()

        content = Text()

        content.append("Status: ")
        content.append(
            data.state,
            style=self._status_style(data.state),
        )
        content.append("\n")

        content.append("System: ")
        content.append(
            data.system_state,
            style=self._status_style(
                data.system_state
            ),
        )
        content.append("\n")

        content.append("Network: ")
        content.append(
            data.network_state,
            style=self._status_style(
                data.network_state
            ),
        )
        content.append("\n")

        unhealthy_interfaces = (
            data.unhealthy_interfaces
        )

        content.append("Issues: ")
        content.append(
            str(len(unhealthy_interfaces))
        )

        if unhealthy_interfaces:
            interface = unhealthy_interfaces[0]

            content.append("\n")
            content.append(
                f"{interface.interface}: "
            )
            content.append(
                interface.state,
                style=self._status_style(
                    interface.state
                ),
            )

            content.append("\n")
            content.append("Reason: ")
            content.append(
                interface.reason
            )

            if interface.error_rate is not None:
                content.append("\n")
                content.append(
                    f"Errors: {interface.error_rate:.2f}/s"
                )

            if interface.drop_rate is not None:
                content.append("\n")
                content.append(
                    f"Drops: {interface.drop_rate:.2f}/s"
                )

        return Panel(
            content,
            title="NODE HEALTH",
            border_style=self._border_style(
                data.state
            ),
        )

    def _render_unavailable(self) -> Panel:
        """Renderiza el panel cuando no existe diagnóstico NOC."""

        content = Text()

        content.append("Status: ")
        content.append(
            "UNKNOWN",
            style=self._status_style(
                "UNKNOWN"
            ),
        )
        content.append("\n")
        content.append("System: UNKNOWN\n")
        content.append("Network: UNKNOWN\n")
        content.append("Issues: 0")

        return Panel(
            content,
            title="NODE HEALTH",
            border_style=self._border_style(
                "UNKNOWN"
            ),
        )

    @classmethod
    def _status_style(
        cls,
        state: str,
    ) -> str:
        """Obtiene el estilo visual de un estado."""

        return cls._STATUS_STYLES.get(
            state,
            "bold dim",
        )

    @classmethod
    def _border_style(
        cls,
        state: str,
    ) -> str:
        """Obtiene el estilo del borde."""

        return cls._BORDER_STYLES.get(
            state,
            "blue",
        )
