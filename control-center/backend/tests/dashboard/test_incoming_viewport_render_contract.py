"""Contract tests for INCOMING viewport rendering."""

import inspect

from rich.console import Console

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.renderers.incoming_panel_renderer import (
    IncomingPanelRenderer,
)


def make_data():
    paths = (
        "ejtv",
        "enlace",
        "impact",
        "test-04",
        "test-05",
        "test-06",
        "test-07",
    )

    return IncomingPanelData(
        rows=tuple(
            IncomingRowData(
                path_name=path,
                source="publisher",
                status="ready",
                bitrate_receive_mbps=6.0,
                health_status=None,
            )
            for path in paths
        )
    )


def render_text(panel):
    console = Console(
        width=160,
        height=40,
        force_terminal=False,
        color_system=None,
        record=True,
    )

    console.print(panel)

    return console.export_text()


def test_incoming_renderer_accepts_optional_viewport():
    signature = inspect.signature(IncomingPanelRenderer.render)

    assert "viewport" in signature.parameters
    assert signature.parameters["viewport"].default is None


def test_incoming_renderer_displays_only_viewport_rows():
    panel = IncomingPanelRenderer().render(
        make_data(),
        selected_path_name="test-05",
        viewport=PanelViewport(offset=3, page_size=3),
    )

    text = render_text(panel)

    assert "test-04" in text
    assert "test-05" in text
    assert "test-06" in text

    assert "ejtv" not in text
    assert "enlace" not in text
    assert "impact" not in text
    assert "test-07" not in text


def test_incoming_renderer_without_viewport_preserves_all_rows():
    panel = IncomingPanelRenderer().render(make_data())

    text = render_text(panel)

    for path in (
        "ejtv",
        "enlace",
        "impact",
        "test-04",
        "test-05",
        "test-06",
        "test-07",
    ):
        assert path in text


def test_incoming_renderer_shows_window_position():
    panel = IncomingPanelRenderer().render(
        make_data(),
        viewport=PanelViewport(offset=3, page_size=3),
    )

    text = render_text(panel)

    assert "4-6" in text
    assert "7" in text


def test_dashboard_renderer_accepts_incoming_viewport():
    signature = inspect.signature(DashboardRenderer.render)

    assert "incoming_viewport" in signature.parameters


def test_dashboard_renderer_forwards_viewport_to_incoming_only():
    source = inspect.getsource(DashboardRenderer.render)

    assert "viewport=incoming_viewport" in source


def test_application_passes_persistent_viewport_to_renderer():
    source = inspect.getsource(DashboardApplication.run_once)

    assert "incoming_viewport=self.incoming_viewport" in source
