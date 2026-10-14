from io import StringIO

from rich.console import Console

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.signal_detail_renderer import (
    SignalDetailRenderer,
)


def test_compact_detail_preserves_operational_visibility():
    data = IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="enlace",
                source="Encoder ENLACE",
                status="ready",
                bitrate_receive_mbps=3.75,
                health_status=None,
                protocol="SRT",
                remote_address="192.0.2.10:8050",
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
        width=100,
        height=12,
        force_terminal=False,
        color_system=None,
    ).print(panel, height=12)

    screen = output.getvalue()

    assert "enlace" in screen
    assert "3.75 Mbps" in screen
    assert "Health" in screen
    assert "2 WARNING" in screen
    assert "SRT" in screen
