"""Contract for optional INCOMING V2 renderer geometry."""

from unittest.mock import Mock

import pytest
from rich.panel import Panel

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
from app.dashboard.services.incoming_vertical_geometry_policy import (
    IncomingVerticalGeometryPolicy,
)


def render_with_geometry(
    *,
    terminal_height: int,
    signal_count: int,
    maximum_visible_rows: int = 8,
):
    renderer = DashboardRenderer()

    renderer._incoming_panel_renderer = Mock()
    renderer._signal_detail_renderer = Mock()

    renderer._incoming_panel_renderer.render.return_value = Panel(
        "LIST DATA",
        title="INCOMING SIGNALS",
    )

    renderer._signal_detail_renderer.render.return_value = Panel(
        "DETAIL DATA",
        title="SIGNAL DETAIL",
    )

    geometry = IncomingVerticalGeometryPolicy().calculate(
        terminal_height=terminal_height,
        signal_count=signal_count,
        maximum_visible_rows=maximum_visible_rows,
    )

    layout = renderer.render(
        Mock(incoming=Mock()),
        terminal_navigation_state=TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        ),
        incoming_selection_state=IncomingSelectionState(
            selected_path_name="ejtv",
        ),
        incoming_visible_capacity=geometry.visible_rows,
        incoming_vertical_geometry=geometry,
        terminal_width=122,
    )

    return layout, geometry


def test_geometry_allocates_compact_list_and_expanded_detail():
    layout, geometry = render_with_geometry(
        terminal_height=30,
        signal_count=3,
    )

    assert geometry.list_height == 6
    assert geometry.detail_height == 21

    assert layout["incoming"]["incoming_list"].size == 6
    assert layout["incoming"]["signal_detail"].size == 21


@pytest.mark.parametrize(
    "terminal_height,signal_count",
    (
        (24, 3),
        (30, 3),
        (30, 8),
        (40, 20),
    ),
)
def test_renderer_respects_geometry_allocation(
    terminal_height,
    signal_count,
):
    layout, geometry = render_with_geometry(
        terminal_height=terminal_height,
        signal_count=signal_count,
    )

    assert (
        layout["incoming"]["incoming_list"].size
        == geometry.list_height
    )

    assert (
        layout["incoming"]["signal_detail"].size
        == geometry.detail_height
    )


def test_geometry_zero_capacity_preserves_detail():
    layout, geometry = render_with_geometry(
        terminal_height=12,
        signal_count=20,
    )

    assert geometry.visible_rows == 0
    assert geometry.detail_height >= 8

    assert (
        layout["incoming"]["signal_detail"].size
        == geometry.detail_height
    )
