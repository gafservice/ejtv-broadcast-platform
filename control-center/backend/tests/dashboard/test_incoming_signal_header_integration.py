"""INCOMING V2 contextual header integration contract."""

from unittest.mock import Mock

from rich.panel import Panel
from rich.text import Text

from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.domain.streaming.health import HealthStatus


def make_incoming():
    return IncomingPanelData(
        rows=(
            IncomingRowData(
                path_name="ejtv",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=4.75,
                health_status=HealthStatus.HEALTHY,
                protocol="UDP",
            ),
            IncomingRowData(
                path_name="enlace",
                source="MPEG-TS",
                status="ACTIVE",
                bitrate_receive_mbps=3.50,
                health_status=HealthStatus.HEALTHY,
                protocol="UDP",
            ),
        ),
    )


def render_for_selection(selected_path_name):
    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._incoming_panel_renderer.render.return_value = Panel(
        "INCOMING LIST",
        title="INCOMING SIGNALS",
    )

    renderer._signal_detail_renderer = Mock()
    renderer._signal_detail_renderer.render.return_value = Panel(
        "EXISTING DETAIL CONTENT",
        title="SIGNAL DETAIL",
    )

    data = Mock()
    data.incoming = make_incoming()

    layout = renderer.render(
        data,
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name=selected_path_name,
        ),
        incoming_visible_capacity=5,
        terminal_width=120,
    )

    return layout["incoming"]["signal_detail"].renderable


def test_signal_header_is_rich_text():
    detail = render_for_selection("ejtv")

    assert isinstance(detail.title, Text)


def test_signal_header_displays_selected_path():
    detail = render_for_selection("ejtv")

    assert "ejtv" in detail.title.plain


def test_signal_header_displays_operational_status():
    detail = render_for_selection("ejtv")

    assert "ACTIVE" in detail.title.plain


def test_signal_header_displays_canonical_health():
    detail = render_for_selection("ejtv")

    assert "HEALTHY" in detail.title.plain


def test_signal_header_changes_with_selection():
    ejtv = render_for_selection("ejtv")
    enlace = render_for_selection("enlace")

    assert "ejtv" in ejtv.title.plain
    assert "enlace" in enlace.title.plain
    assert "ejtv" not in enlace.title.plain


def test_signal_header_preserves_existing_detail_content():
    detail = render_for_selection("ejtv")

    assert isinstance(detail, Panel)
    assert detail.renderable == "EXISTING DETAIL CONTENT"


def test_signal_header_handles_missing_selection():
    detail = render_for_selection(None)

    assert "No incoming signal selected" in detail.title.plain
