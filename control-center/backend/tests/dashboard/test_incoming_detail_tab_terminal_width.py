"""Terminal width propagation contract for INCOMING detail tabs."""

import pytest

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
)
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)
from app.dashboard.renderers.dashboard_renderer import DashboardRenderer

from tests.dashboard.test_dashboard_renderer import (
    build_dashboard_data,
)


@pytest.mark.parametrize(
    "terminal_width",
    (120, 80, 55, 30, 25, 20),
)
def test_renderer_accepts_actual_terminal_width(terminal_width):
    renderer = DashboardRenderer()

    layout = renderer.render(
        build_dashboard_data(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=IncomingDetailTab.VIDEO,
        ),
        terminal_width=terminal_width,
    )

    detail = layout["incoming"]["signal_detail"].renderable

    assert detail.subtitle is not None

    available_width = max(1, terminal_width - 4)

    assert len(detail.subtitle.plain) <= available_width


@pytest.mark.parametrize(
    "terminal_width",
    (120, 80, 55, 30, 25),
)
def test_six_tabs_remain_addressable(terminal_width):
    renderer = DashboardRenderer()

    layout = renderer.render(
        build_dashboard_data(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_detail_tab_state=IncomingDetailTabState(
            active_tab=IncomingDetailTab.AUDIO,
        ),
        terminal_width=terminal_width,
    )

    detail = layout["incoming"]["signal_detail"].renderable

    for number in "123456":
        assert number in detail.subtitle.plain


def test_default_render_contract_remains_compatible():
    renderer = DashboardRenderer()

    layout = renderer.render(
        build_dashboard_data(),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
    )

    detail = layout["incoming"]["signal_detail"].renderable

    assert detail.subtitle is not None


@pytest.mark.parametrize(
    "invalid_width",
    (0, -1),
)
def test_invalid_terminal_width_is_rejected(invalid_width):
    renderer = DashboardRenderer()

    with pytest.raises(ValueError):
        renderer.render(
            build_dashboard_data(),
            terminal_navigation_state=TerminalNavigationState(
                active_view=TerminalView.INCOMING,
            ),
            terminal_width=invalid_width,
        )
