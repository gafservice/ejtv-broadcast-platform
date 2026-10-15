"""INCOMING V2: full Live resize and selection preservation."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.dashboard.application import DashboardApplication
from app.dashboard.models.dashboard_navigation_state import (
    DashboardNavigationState,
)
from app.dashboard.models.incoming_panel import (
    IncomingPanelData,
    IncomingRowData,
)
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport
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


PATHS = tuple(
    f"signal-{index:02d}"
    for index in range(1, 23)
)

DIMENSIONS = (
    (122, 30),
    (100, 20),
    (140, 40),
    (122, 30),
)


class ResizeLive:
    def __init__(self):
        self.index = 0
        self.console = SimpleNamespace(
            size=SimpleNamespace(
                width=DIMENSIONS[0][0],
                height=DIMENSIONS[0][1],
            )
        )
        self.updates = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def update(self, renderable, *, refresh):
        assert refresh is True

        self.updates.append(renderable)
        self.index += 1

        if self.index < len(DIMENSIONS):
            width, height = DIMENSIONS[self.index]

            self.console.size = SimpleNamespace(
                width=width,
                height=height,
            )


def test_v2_live_resize_preserves_selection_and_capture_cadence():
    application = DashboardApplication.__new__(
        DashboardApplication
    )

    application._terminal_navigation_state = (
        TerminalNavigationState(
            active_view=TerminalView.INCOMING,
        )
    )

    application._navigation_state = DashboardNavigationState()
    application._navigation_totals = Mock()
    application._navigation_controller = Mock()

    application._incoming_selection_state = (
        IncomingSelectionState(
            selected_path_name="signal-18",
        )
    )

    application._incoming_path_names = ()
    application._incoming_viewport = PanelViewport(
        page_size=5,
    )

    application._keyboard_input = None
    application._key_parser = None

    incoming = IncomingPanelData(
        rows=tuple(
            IncomingRowData(
                path_name=path,
                source="publisher",
                status="ready",
                bitrate_receive_mbps=6.0,
                health_status=None,
                protocol="SRT",
                remote_address="192.0.2.10:9000",
            )
            for path in PATHS
        )
    )

    dashboard_data = replace(
        build_dashboard_data(),
        incoming=incoming,
    )

    captures = []
    geometry_history = []

    def fake_build_dashboard():
        captures.append(len(captures) + 1)
        application.reconcile_incoming_selection(PATHS)
        return dashboard_data

    renderer = DashboardRenderer()
    real_render = renderer.render

    def capture_render(data, **kwargs):
        geometry = kwargs.get(
            "incoming_vertical_geometry"
        )

        geometry_history.append(
            (
                geometry,
                kwargs["incoming_viewport"],
                kwargs["incoming_selection_state"],
            )
        )

        return real_render(data, **kwargs)

    application.build_dashboard = fake_build_dashboard
    application._dashboard_renderer = renderer

    live = ResizeLive()

    with (
        patch(
            "app.dashboard.application.Live",
            return_value=live,
        ),
        patch(
            "app.dashboard.application.sleep",
        ),
        patch.object(
            renderer,
            "render",
            side_effect=capture_render,
        ),
    ):
        application.run(
            refresh_interval_seconds=0,
            max_iterations=len(DIMENSIONS),
        )

    assert len(captures) == len(DIMENSIONS)
    assert len(live.updates) == len(DIMENSIONS)
    assert len(geometry_history) == len(DIMENSIONS)

    expected_rows = (8, 2, 8, 8)

    for index, (
        geometry,
        viewport,
        selection,
    ) in enumerate(geometry_history):

        assert geometry is not None

        assert geometry.visible_rows == expected_rows[index]

        width, height = DIMENSIONS[index]

        assert (
            geometry.header_height
            + geometry.list_height
            + geometry.detail_height
            == height
        )

        assert geometry.visible_rows <= 8

        assert (
            selection.selected_path_name
            == "signal-18"
        )

        assert viewport.page_size == expected_rows[index]

        start, end = viewport.bounds(len(PATHS))

        assert "signal-18" in PATHS[start:end]

    assert (
        application.incoming_selection_state.selected_path_name
        == "signal-18"
    )

    application._navigation_controller.apply.assert_not_called()
