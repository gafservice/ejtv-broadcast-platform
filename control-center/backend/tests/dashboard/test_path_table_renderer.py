"""Pruebas para PathTableRenderer."""

from rich.table import Table

from app.dashboard.models import PathRowData
from app.dashboard.renderers.path_table_renderer import (
    PathTableRenderer,
)


def test_path_table_renderer_can_be_created() -> None:
    renderer = PathTableRenderer()

    assert renderer is not None


def test_render_returns_rich_table() -> None:
    renderer = PathTableRenderer()

    rows = (
        PathRowData(
            name="enlace",
            source="UDP",
            readers=5,
            inbound_bitrate_bps=8_000_000,
            outbound_bitrate_bps=40_000_000,
            status="ACTIVE",
            quality="AVAILABLE",
        ),
    )

    table = renderer.render(rows)

    assert isinstance(table, Table)
