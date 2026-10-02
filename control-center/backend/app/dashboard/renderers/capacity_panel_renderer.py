"""Rich renderer for canonical NOC capacity."""

from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.capacity_panel import (
    CapacityPanelData,
)


class CapacityPanelRenderer:
    """Render canonical capacity without reinterpreting it."""

    def render(
        self,
        data: CapacityPanelData,
    ) -> Panel:
        table = Table(
            expand=True,
            show_header=True,
            header_style="bold",
        )

        table.add_column("Resource")
        table.add_column("Allocated", justify="right")
        table.add_column("Reserved", justify="right")
        table.add_column("Available", justify="right")
        table.add_column("Maximum", justify="right")
        table.add_column("Use", justify="right")

        for resource in data.resources:
            table.add_row(
                resource.resource,
                self._format_value(
                    resource.allocated,
                    resource.unit,
                ),
                self._format_value(
                    resource.reserved,
                    resource.unit,
                ),
                self._format_value(
                    resource.available,
                    resource.unit,
                ),
                self._format_value(
                    resource.maximum,
                    resource.unit,
                ),
                f"{resource.utilization_percent:.1f}%",
            )

        return Panel(
            table,
            title="CAPACITY",
        )

    @staticmethod
    def _format_value(
        value: float,
        unit: str,
    ) -> str:
        if unit == "bytes":
            size = float(value)

            for suffix in (
                "B",
                "KiB",
                "MiB",
                "GiB",
                "TiB",
            ):
                if abs(size) < 1024.0 or suffix == "TiB":
                    return f"{size:.2f} {suffix}"

                size /= 1024.0

        return f"{value:g} {unit}"
