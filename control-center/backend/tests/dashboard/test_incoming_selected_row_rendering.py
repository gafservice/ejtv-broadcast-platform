"""Contract tests for INCOMING selected-row presentation."""

from rich.panel import Panel
from rich.table import Table

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)


def make_row(path_name: str) -> IncomingRowData:
    return IncomingRowData(
        path_name=path_name,
        source="TEST",
        status="ACTIVE",
        bitrate_receive_mbps=1.0,
        health_status=None,
    )


def make_panel(
    *path_names: str,
) -> IncomingPanelData:
    return IncomingPanelData(
        rows=tuple(
            make_row(name)
            for name in path_names
        ),
    )


def render_table(
    data: IncomingPanelData,
    selected_path_name: str | None,
) -> Table:
    panel = IncomingPanelRenderer().render(
        data,
        selected_path_name=selected_path_name,
    )

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Table)

    return panel.renderable


def test_selected_incoming_row_has_exclusive_style():
    table = render_table(
        make_panel("ejtv", "enlace", "impact"),
        selected_path_name="enlace",
    )

    assert len(table.rows) == 3

    assert table.rows[0].style is None
    assert table.rows[1].style is not None
    assert table.rows[2].style is None


def test_none_selection_does_not_highlight_rows():
    table = render_table(
        make_panel("ejtv", "enlace", "impact"),
        selected_path_name=None,
    )

    assert all(
        row.style is None
        for row in table.rows
    )


def test_unknown_selection_does_not_highlight_rows():
    table = render_table(
        make_panel("ejtv", "enlace", "impact"),
        selected_path_name="unknown",
    )

    assert all(
        row.style is None
        for row in table.rows
    )


def test_selection_follows_path_identity_after_reorder():
    table = render_table(
        make_panel("impact", "ejtv", "enlace"),
        selected_path_name="enlace",
    )

    assert table.rows[0].style is None
    assert table.rows[1].style is None
    assert table.rows[2].style is not None


def test_legacy_render_call_remains_supported():
    panel = IncomingPanelRenderer().render(
        make_panel("ejtv", "enlace"),
    )

    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Table)

    assert all(
        row.style is None
        for row in panel.renderable.rows
    )
