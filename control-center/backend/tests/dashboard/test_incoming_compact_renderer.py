"""Contract tests for compact INCOMING rendering."""

from inspect import signature

from rich.table import Table

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)


def sample_data():
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="publisher",
                status="ready",
                bitrate_receive_mbps=6.0,
                health_status=None,
                protocol="SRT",
                remote_address="192.0.2.10:9000",
            ),
        ),
    )


def test_renderer_accepts_presentation_mode():
    parameters = signature(
        IncomingPanelRenderer.render
    ).parameters

    assert "presentation_mode" in parameters
    assert parameters["presentation_mode"].default == "full"


def test_compact_renderer_has_seven_columns():
    panel = IncomingPanelRenderer().render(
        sample_data(),
        selected_path_name="ejtv",
        presentation_mode="compact",
    )

    assert isinstance(panel.renderable, Table)

    columns = [
        column.header
        for column in panel.renderable.columns
    ]

    assert columns == [
        "Path",
        "Source",
        "Protocol",
        "Receive",
        "Status",
        "Health",
        "Alarms",
    ]


def test_compact_renderer_preserves_canonical_values():
    panel = IncomingPanelRenderer().render(
        sample_data(),
        selected_path_name="ejtv",
        presentation_mode="compact",
    )

    table = panel.renderable

    assert len(table.rows) == 1
    assert table.rows[0].style == "reverse"

    values = [
        column._cells[0]
        for column in table.columns
    ]

    assert values == [
        "ejtv",
        "publisher",
        "SRT",
        "6.00 Mbps",
        "ready",
        "N/A",
        "—",
    ]


def test_full_renderer_retains_eleven_columns():
    panel = IncomingPanelRenderer().render(
        sample_data(),
        presentation_mode="full",
    )

    columns = [
        column.header
        for column in panel.renderable.columns
    ]

    assert columns == [
        "Path",
        "Source",
        "Protocol",
        "Origin",
        "Receive",
        "Status",
        "Health",
        "Alarms",
        "Since",
        "Duration",
        "Reason",
    ]
