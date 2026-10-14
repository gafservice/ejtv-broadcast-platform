"""Adaptive INCOMING application integration contract."""

from inspect import signature

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport
from app.dashboard.services.incoming_presentation_policy import (
    IncomingPresentationPolicy,
)


def test_run_once_accepts_optional_terminal_dimensions():
    """Dimension injection must preserve the existing run_once API."""

    parameters = signature(DashboardApplication.run_once).parameters

    assert "terminal_width" in parameters
    assert "incoming_height" in parameters

    assert parameters["terminal_width"].default is None
    assert parameters["incoming_height"].default is None


def test_adaptive_viewport_preserves_selected_identity():
    """Resizing must not change the selected signal."""

    paths = (
        "ejtv",
        "enlace",
        "impact",
        "test-04",
        "test-05",
        "test-06",
        "test-07",
    )

    selection = IncomingSelectionState(
        selected_path_name="test-05",
    )

    policy = IncomingPresentationPolicy()

    config = policy.calculate(
        terminal_width=100,
        incoming_height=7,
    )

    assert config.mode == "operational"
    assert config.page_size == 4

    viewport = PanelViewport(
        offset=0,
        page_size=config.page_size,
    )

    updated = selection.ensure_visible(
        viewport,
        paths,
    )

    start, end = updated.bounds(len(paths))

    assert selection.selected_path_name == "test-05"
    assert "test-05" in paths[start:end]
    assert updated.page_size == 4


def test_adaptive_viewport_handles_resize():
    """Selection must survive a change in visible capacity."""

    paths = tuple(f"signal-{index:02d}" for index in range(22))

    selection = IncomingSelectionState(
        selected_path_name="signal-18",
    )

    policy = IncomingPresentationPolicy()

    compact = policy.calculate(
        terminal_width=100,
        incoming_height=7,
    )

    expanded = policy.calculate(
        terminal_width=160,
        incoming_height=27,
    )

    compact_viewport = selection.ensure_visible(
        PanelViewport(page_size=compact.page_size),
        paths,
    )

    expanded_viewport = selection.ensure_visible(
        PanelViewport(
            offset=compact_viewport.offset,
            page_size=expanded.page_size,
        ),
        paths,
    )

    start, end = expanded_viewport.bounds(len(paths))

    assert selection.selected_path_name == "signal-18"
    assert "signal-18" in paths[start:end]
    assert expanded_viewport.page_size == 24


def test_zero_capacity_requires_explicit_integration_handling():
    """The policy may report zero, but PanelViewport cannot use it."""

    config = IncomingPresentationPolicy().calculate(
        terminal_width=100,
        incoming_height=3,
    )

    assert config.page_size == 0


def test_run_once_preserves_adaptive_capacity_after_capture(monkeypatch):
    """Capture reconciliation must preserve the adaptive page size."""

    from types import SimpleNamespace

    paths = tuple(f"signal-{index:02d}" for index in range(22))

    application = object.__new__(DashboardApplication)

    application._incoming_selection_state = IncomingSelectionState(
        selected_path_name="signal-18",
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

            viewport = kwargs["incoming_viewport"]
            selection = kwargs["incoming_selection_state"]

            assert viewport.page_size == 4
            assert selection.selected_path_name == "signal-18"

            start, end = viewport.bounds(len(paths))

            assert "signal-18" in paths[start:end]

            return SimpleNamespace(success=True)

    application._dashboard_renderer = FakeRenderer()

    monkeypatch.setattr(
        application,
        "build_dashboard",
        fake_build_dashboard,
    )

    result = application.run_once(
        terminal_width=100,
        incoming_height=7,
    )

    assert result.success is True
    assert calls["capture"] == 1
    assert calls["render"] == 1


def test_run_once_preserves_legacy_call_without_dimensions(monkeypatch):
    """Existing callers may continue invoking run_once without arguments."""

    from types import SimpleNamespace

    application = object.__new__(DashboardApplication)

    application._incoming_selection_state = IncomingSelectionState()
    application._incoming_path_names = ()
    application._incoming_viewport = PanelViewport(page_size=5)

    application._navigation_state = None
    application._terminal_navigation_state = None

    calls = {"capture": 0}

    def fake_build_dashboard():
        calls["capture"] += 1
        return object()

    class FakeRenderer:
        def render(self, data, **kwargs):
            assert kwargs["incoming_viewport"].page_size == 5
            return SimpleNamespace(success=True)

    application._dashboard_renderer = FakeRenderer()

    monkeypatch.setattr(
        application,
        "build_dashboard",
        fake_build_dashboard,
    )

    result = application.run_once()

    assert result.success is True
    assert calls["capture"] == 1
