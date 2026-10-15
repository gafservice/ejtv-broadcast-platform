"""INCOMING V2 selected signal header contract."""

from io import StringIO

from rich.console import Console

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.renderers.incoming_signal_header_renderer import (
    IncomingSignalHeaderRenderer,
)
from app.domain.streaming.health import HealthStatus


def render_text(renderable, width=100):
    output = StringIO()

    Console(
        file=output,
        width=width,
        force_terminal=False,
        color_system=None,
    ).print(renderable)

    return output.getvalue()


def make_data(
    *,
    status="ACTIVE",
    health_status=HealthStatus.HEALTHY,
):
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="MPEG-TS",
                status=status,
                bitrate_receive_mbps=4.75,
                health_status=health_status,
                protocol="UDP",
            ),
        ),
    )


def test_header_displays_selected_signal_identity():
    result = IncomingSignalHeaderRenderer().render(
        make_data(),
        selected_path_name="ejtv",
    )

    screen = render_text(result)

    assert "SIGNAL DETAIL" in screen
    assert "ejtv" in screen


def test_header_displays_canonical_operational_status():
    result = IncomingSignalHeaderRenderer().render(
        make_data(status="ACTIVE"),
        selected_path_name="ejtv",
    )

    assert "ACTIVE" in render_text(result)


def test_header_displays_canonical_health_status():
    result = IncomingSignalHeaderRenderer().render(
        make_data(health_status=HealthStatus.HEALTHY),
        selected_path_name="ejtv",
    )

    assert "HEALTHY" in render_text(result)


def test_header_preserves_unavailable_health():
    result = IncomingSignalHeaderRenderer().render(
        make_data(health_status=None),
        selected_path_name="ejtv",
    )

    assert "N/A" in render_text(result)


def test_header_handles_missing_selection():
    result = IncomingSignalHeaderRenderer().render(
        make_data(),
        selected_path_name=None,
    )

    assert "No incoming signal selected" in render_text(result)


def test_header_handles_unknown_selection():
    result = IncomingSignalHeaderRenderer().render(
        make_data(),
        selected_path_name="unknown-path",
    )

    assert "No incoming signal selected" in render_text(result)


def test_header_does_not_mutate_input_data():
    data = make_data()
    before = data

    IncomingSignalHeaderRenderer().render(
        data,
        selected_path_name="ejtv",
    )

    assert data == before
