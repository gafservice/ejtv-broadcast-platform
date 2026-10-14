from io import StringIO
from unittest.mock import Mock

from rich.console import Console
from rich.panel import Panel

from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer


def test_zero_capacity_notice_visible_at_24_lines():
    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._signal_detail_renderer = Mock()

    renderer._incoming_panel_renderer.render.return_value = Panel(
        "LIST ROW: enlace",
        title="INCOMING SIGNALS",
    )

    renderer._signal_detail_renderer.render.return_value = Panel(
        "DETAIL DATA: enlace",
        title="SIGNAL DETAIL",
    )

    selection = IncomingSelectionState(
        selected_path_name="enlace",
    )

    layout = renderer.render(
        Mock(incoming=Mock()),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=selection,
        incoming_visible_capacity=0,
    )

    output = StringIO()

    console = Console(
        file=output,
        width=100,
        height=24,
        force_terminal=False,
        color_system=None,
    )

    console.print(layout)

    screen = output.getvalue()

    assert "Insufficient terminal height" in screen
    assert "SIGNAL DETAIL" in screen
    assert "DETAIL DATA: enlace" in screen
    assert selection.selected_path_name == "enlace"
