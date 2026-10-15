"""Selected incoming signal header presentation."""

from __future__ import annotations

from rich.text import Text

from app.dashboard.models.incoming_panel import IncomingPanelData


class IncomingSignalHeaderRenderer:
    """Present canonical selected-signal identity and status."""

    def render(
        self,
        data: IncomingPanelData | None,
        *,
        selected_path_name: str | None = None,
    ) -> Text:
        """Return a Rich header without modifying domain state."""

        selected = None

        if (
            isinstance(data, IncomingPanelData)
            and selected_path_name is not None
        ):
            selected = next(
                (
                    row
                    for row in data.rows
                    if row.path_name == selected_path_name
                ),
                None,
            )

        if selected is None:
            return Text(
                "SIGNAL DETAIL · No incoming signal selected.",
                style="dim",
                no_wrap=True,
                overflow="ellipsis",
            )

        operational_status = (
            str(selected.status)
            if selected.status is not None
            and selected.status != ""
            else "N/A"
        )

        health_status = (
            selected.health_status.value
            if selected.health_status is not None
            else "N/A"
        )

        header = Text(
            no_wrap=True,
            overflow="ellipsis",
        )

        header.append(
            "SIGNAL DETAIL",
            style="bold",
        )

        header.append(" · ")

        header.append(
            selected.path_name,
            style="bold cyan",
        )

        header.append("    ")

        header.append(
            operational_status,
            style="bold",
        )

        header.append(" · ")

        header.append(
            health_status,
            style="bold",
        )

        return header
