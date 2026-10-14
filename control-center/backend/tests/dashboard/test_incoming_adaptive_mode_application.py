"""Contract: application forwards adaptive presentation mode."""

from types import SimpleNamespace

import pytest

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport


@pytest.mark.parametrize(
    "width,height,expected_mode,expected_page_size",
    [
        (100, 7, "operational", 4),
        (120, 17, "operational", 14),
    ],
)
def test_application_forwards_adaptive_presentation_mode(
    monkeypatch,
    width,
    height,
    expected_mode,
    expected_page_size,
):
    application = object.__new__(DashboardApplication)

    paths = tuple(
        f"signal-{index:02d}"
        for index in range(22)
    )

    application._incoming_selection_state = (
        IncomingSelectionState(
            selected_path_name="signal-18",
        )
    )

    application._incoming_path_names = paths
    application._incoming_viewport = PanelViewport(
        page_size=5
    )

    application._navigation_state = None
    application._terminal_navigation_state = None

    calls = {
        "capture": 0,
        "render": 0,
    }

    def fake_build_dashboard():
        calls["capture"] += 1

        application.reconcile_incoming_selection(
            paths
        )

        return object()

    class FakeRenderer:
        def render(self, data, **kwargs):
            calls["render"] += 1

            assert (
                kwargs.get("incoming_presentation_mode")
                == expected_mode
            )

            viewport = kwargs["incoming_viewport"]

            assert viewport.page_size == expected_page_size

            start, end = viewport.bounds(
                len(paths)
            )

            assert "signal-18" in paths[start:end]

            return SimpleNamespace(success=True)

    application._dashboard_renderer = FakeRenderer()

    monkeypatch.setattr(
        application,
        "build_dashboard",
        fake_build_dashboard,
    )

    result = application.run_once(
        terminal_width=width,
        incoming_height=height,
    )

    assert result.success is True
    assert calls["capture"] == 1
    assert calls["render"] == 1
