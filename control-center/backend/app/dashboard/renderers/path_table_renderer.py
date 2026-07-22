"""Renderizador de la tabla de paths."""

from rich.table import Table

from app.dashboard.models import PathRowData


class PathTableRenderer:
    """Renderiza el estado de los paths en una tabla de Rich."""

    def render(self, rows: tuple[PathRowData, ...]) -> Table:
        """Convierte una colección de PathRowData en una tabla."""

        table = Table(title="PATHS")

        table.add_column("Path")
        table.add_column("Source")
        table.add_column("Readers")
        table.add_column("Inbound")
        table.add_column("Outbound")
        table.add_column("Status")
        table.add_column("Quality")

        for row in rows:
            table.add_row(
                row.name,
                row.source,
                str(row.readers),
                self._format_bitrate(row.inbound_bitrate_bps),
                self._format_bitrate(row.outbound_bitrate_bps),
                row.status,
                row.quality,
            )

        return table

    @staticmethod
    def _format_bitrate(bitrate_bps: float | None) -> str:
        """Convierte bits por segundo a megabits por segundo."""

        if bitrate_bps is None:
            return "N/A"

        return f"{bitrate_bps / 1_000_000:.2f} Mbps"
