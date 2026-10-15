"""Contract tests for application-to-renderer INCOMING tab state."""

from unittest.mock import Mock

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.models.terminal_navigation_state import (
    TerminalNavigationState,
    TerminalView,
)


def make_application(tab):
    application = object.__new__(DashboardApplication)

    application._navigation_state = Mock()
    application._terminal_navigation_state = TerminalNavigationState(
        active_view=TerminalView.INCOMING,
    )
    application._incoming_selection_state = IncomingSelectionState(
        selected_path_name="enlace",
    )
    application._incoming_detail_tab_state = IncomingDetailTabState(
        active_tab=tab,
    )
    application._incoming_viewport = PanelViewport(page_size=5)

    dashboard_data = object()
    renderer_result = object()

    application.build_dashboard = Mock(
        return_value=dashboard_data,
    )

    application._dashboard_renderer = Mock()
    application._dashboard_renderer.render.return_value = (
        renderer_result
    )

    return application, dashboard_data, renderer_result


def test_run_once_passes_active_tab_to_renderer():
    application, dashboard_data, expected_result = (
        make_application(IncomingDetailTab.VIDEO)
    )

    result = application.run_once()

    assert result is expected_result

    args, kwargs = (
        application._dashboard_renderer.render.call_args
    )

    assert args == (dashboard_data,)

    assert (
        kwargs["incoming_detail_tab_state"].active_tab
        is IncomingDetailTab.VIDEO
    )

    assert (
        kwargs["incoming_selection_state"].selected_path_name
        == "enlace"
    )


def test_run_once_preserves_default_signal_tab():
    application, _, _ = make_application(
        IncomingDetailTab.SIGNAL
    )

    application.run_once()

    kwargs = (
        application._dashboard_renderer.render.call_args.kwargs
    )

    assert (
        kwargs["incoming_detail_tab_state"].active_tab
        is IncomingDetailTab.SIGNAL
    )


def test_run_once_preserves_statistics_tab():
    application, _, _ = make_application(
        IncomingDetailTab.STATISTICS
    )

    application.run_once()

    kwargs = (
        application._dashboard_renderer.render.call_args.kwargs
    )

    assert (
        kwargs["incoming_detail_tab_state"].active_tab
        is IncomingDetailTab.STATISTICS
    )
