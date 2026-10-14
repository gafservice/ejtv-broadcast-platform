"""Contract for zero-capacity INCOMING presentation."""

from types import SimpleNamespace

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport


def test_zero_capacity_is_explicitly_forwarded_to_renderer(
    monkeypatch,
):
    """Do not represent an unavailable list as a visible viewport."""

    application = object.__new__(DashboardApplication)

    paths = ("ejtv", "enlace", "impact")

    application._incoming_selection_state = IncomingSelectionState(
        selected_path_name="enlace",
    )
    application._incoming_path_names = paths
    application._incoming_viewport = PanelViewport(page_size=5)

    application._navigation_state = None
    application._terminal_navigation_state = None

    calls = {"capture": 0, "render": 0}

    def fake_build_dashboard():
        calls["capture"] += 1
        application.reconcile_incoming_selection(paths)
        return object()

    class FakeRenderer:
        def render(self, data, **kwargs):
            calls["render"] += 1

            assert (
                kwargs["incoming_selection_state"].selected_path_name
                == "enlace"
            )

            assert kwargs["incoming_visible_capacity"] == 0

            return SimpleNamespace(success=True)

    application._dashboard_renderer = FakeRenderer()

    monkeypatch.setattr(
        application,
        "build_dashboard",
        fake_build_dashboard,
    )

    result = application.run_once(
        terminal_width=100,
        incoming_height=3,
    )

    assert result.success is True
    assert calls["capture"] == 1
    assert calls["render"] == 1
