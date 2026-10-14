"""Contract tests for operational INCOMING rendering."""

import pytest

from rich.table import Table

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)


@pytest.fixture
def incoming_data():
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=4.70,
                health_status=None,
                protocol="UDP",
                remote_address="10.0.18.51:3000",
            ),
        ),
    )


def test_operational_renderer_has_eight_columns(incoming_data):
    panel = IncomingPanelRenderer().render(
        incoming_data,
        presentation_mode="operational",
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
        "Origin",
        "Receive",
        "Status",
        "Health",
        "Alarms",
    ]


def test_operational_renderer_preserves_values_and_selection(
    incoming_data,
):
    panel = IncomingPanelRenderer().render(
        incoming_data,
        selected_path_name="ejtv",
        presentation_mode="operational",
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
        "MPEG-TS",
        "UDP",
        "10.0.18.51:3000",
        "4.70 Mbps",
        "ACTIVE",
        "N/A",
        "—",
    ]
