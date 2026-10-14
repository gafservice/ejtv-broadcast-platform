from unittest.mock import Mock

from rich.panel import Panel

from app.dashboard.renderers.dashboard_renderer import DashboardRenderer
from app.dashboard.models.incoming_selection_state import IncomingSelectionState
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)


def test_zero_capacity_shows_explicit_notice_without_losing_detail():
    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._signal_detail_renderer = Mock()

    renderer._incoming_panel_renderer.render.return_value = Panel(
        "UNEXPECTED TABLE",
        title="INCOMING SIGNALS",
    )

    renderer._signal_detail_renderer.render.return_value = Panel(
        "SELECTED SIGNAL DETAIL",
        title="SIGNAL DETAIL",
    )

    incoming = Mock()
    data = Mock(incoming=incoming)

    selection = IncomingSelectionState(
        selected_path_name="enlace",
    )

    layout = renderer.render(
        data,
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=selection,
        incoming_visible_capacity=0,
    )

    assert selection.selected_path_name == "enlace"

    assert layout["signal_detail"].renderable.title == "SIGNAL DETAIL"

    incoming_panel = layout["incoming_list"].renderable

    assert isinstance(incoming_panel, Panel)
    assert incoming_panel.title == "INCOMING SIGNALS"

    assert (
        "insufficient terminal height"
        in str(incoming_panel.renderable).lower()
    )

    renderer._signal_detail_renderer.render.assert_called_once_with(
        incoming,
        selected_path_name="enlace",
        compact=True,
    )
