"""Line separation contract for specialized INCOMING detail tabs."""

import pytest

from rich.panel import Panel

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)
from app.dashboard.renderers.dashboard_renderer import (
    DashboardRenderer,
)

from tests.dashboard.test_dashboard_renderer import (
    build_dashboard_data,
)


SPECIALIZED_TABS = (
    IncomingDetailTab.TRANSPORT,
    IncomingDetailTab.VIDEO,
    IncomingDetailTab.AUDIO,
    IncomingDetailTab.EVENTS,
    IncomingDetailTab.STATISTICS,
)


@pytest.mark.parametrize("tab", SPECIALIZED_TABS)
def test_signal_and_metrics_appear_on_separate_lines(tab):
    renderer = DashboardRenderer()

    layout = renderer.render(
        build_dashboard_data(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name="enlace",
        ),
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=tab,
        ),
        terminal_width=80,
    )

    detail = layout["incoming"]["signal_detail"].renderable

    assert isinstance(detail, Panel)

    assert detail.renderable == (
        "Signal: enlace\n"
        "Metrics: N/A"
    )


@pytest.mark.parametrize("tab", SPECIALIZED_TABS)
def test_no_selection_message_is_preserved(tab):
    renderer = DashboardRenderer()

    layout = renderer.render(
        build_dashboard_data(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=tab,
        ),
        terminal_width=80,
    )

    detail = layout["incoming"]["signal_detail"].renderable

    assert isinstance(detail, Panel)

    assert detail.renderable == (
        "No incoming signal selected."
    )
