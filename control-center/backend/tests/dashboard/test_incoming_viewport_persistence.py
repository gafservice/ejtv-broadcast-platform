"""Contract tests for persistent INCOMING viewport state."""

from app.dashboard.application import DashboardApplication
from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport


def make_application():
    """Create a minimal application without activating external services."""
    app = DashboardApplication.__new__(DashboardApplication)

    app._incoming_selection_state = IncomingSelectionState()
    app._incoming_path_names = ()

    return app


def test_incoming_viewport_is_independent_and_persistent():
    app = make_application()

    app._incoming_viewport = PanelViewport(
        offset=1,
        page_size=3,
    )

    assert app.incoming_viewport.offset == 1
    assert app.incoming_viewport.page_size == 3

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="impact",
    )

    app.reconcile_incoming_selection(
        ("ejtv", "enlace", "impact", "test-04", "test-05")
    )

    assert app.incoming_viewport.offset == 1


def test_incoming_viewport_follows_selected_identity():
    app = make_application()

    app._incoming_viewport = PanelViewport(
        offset=0,
        page_size=3,
    )

    paths = (
        "ejtv",
        "enlace",
        "impact",
        "test-04",
        "test-05",
    )

    app.reconcile_incoming_selection(paths)

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="test-05",
    )

    app.synchronize_incoming_viewport()

    start, end = app.incoming_viewport.bounds(len(paths))

    assert start <= paths.index("test-05") < end


def test_reordering_preserves_selected_identity_and_visibility():
    app = make_application()

    app._incoming_viewport = PanelViewport(
        offset=0,
        page_size=3,
    )

    app.reconcile_incoming_selection(
        ("ejtv", "enlace", "impact", "test-04")
    )

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="impact",
    )

    app.synchronize_incoming_viewport()

    reordered = (
        "impact",
        "test-04",
        "ejtv",
        "enlace",
    )

    app.reconcile_incoming_selection(reordered)

    assert (
        app.incoming_selection_state.selected_path_name
        == "impact"
    )

    start, end = app.incoming_viewport.bounds(len(reordered))

    assert start <= reordered.index("impact") < end


def test_removed_selection_reconciles_and_normalizes_viewport():
    app = make_application()

    app._incoming_viewport = PanelViewport(
        offset=3,
        page_size=3,
    )

    app.reconcile_incoming_selection(
        ("ejtv", "enlace", "impact", "test-04", "test-05", "test-06")
    )

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="test-06",
    )

    app.synchronize_incoming_viewport()

    remaining = (
        "ejtv",
        "enlace",
    )

    app.reconcile_incoming_selection(remaining)

    assert (
        app.incoming_selection_state.selected_path_name
        in remaining
    )

    assert app.incoming_viewport.offset == 0


def test_incoming_viewport_does_not_replace_general_navigation_state():
    app = make_application()

    general_state = object()
    app._navigation_state = general_state

    app._incoming_viewport = PanelViewport(
        offset=0,
        page_size=3,
    )

    app.reconcile_incoming_selection(
        ("ejtv", "enlace", "impact", "test-04")
    )

    app._incoming_selection_state = IncomingSelectionState(
        selected_path_name="test-04",
    )

    app.synchronize_incoming_viewport()

    assert app._navigation_state is general_state
