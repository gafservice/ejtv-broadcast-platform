"""Physical visibility of long complementary fields in compact Signal Detail."""

from io import StringIO

import pytest
from rich.console import Console

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.signal_detail_renderer import (
    SignalDetailRenderer,
)


@pytest.mark.parametrize("width", [40, 60, 80])
def test_compact_long_fields_preserve_critical_and_complementary_rows(width):
    source = "ENLACE PRIMARY ENCODER " * 12
    remote = "encoder-primary-streaming.example.net:8050"

    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="enlace",
                source=source,
                status="ready",
                bitrate_receive_mbps=3.75,
                health_status=None,
                protocol="SRT",
                remote_address=remote,
                alarm_count=2,
                alarm_severity="WARNING",
            ),
        ),
    )

    panel = SignalDetailRenderer().render(
        data,
        selected_path_name="enlace",
        compact=True,
    )

    output = StringIO()

    Console(
        file=output,
        width=width,
        height=12,
        force_terminal=False,
        color_system=None,
    ).print(panel, height=12)

    screen = output.getvalue()

    # Operational information must remain visible.
    assert "enlace" in screen
    assert "Health" in screen
    assert "2 WARNING" in screen
    assert "ready" in screen
    assert "3.75 Mbps" in screen
    assert "SRT" in screen

    # Long complementary fields must retain visible rows.
    assert "Source" in screen
    assert "Remote" in screen

    # Original data must remain unchanged.
    assert data.rows[0].source == source
    assert data.rows[0].remote_address == remote
