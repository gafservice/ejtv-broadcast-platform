"""Contract tests for INCOMING selection viewport synchronization."""

from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)
from app.dashboard.models.panel_viewport import PanelViewport


def test_selected_incoming_path_is_kept_inside_viewport():
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
        selected_path_name="test-06",
    )

    viewport = PanelViewport(
        offset=0,
        page_size=3,
    )

    updated = selection.ensure_visible(
        viewport,
        paths,
    )

    start, end = updated.bounds(len(paths))

    assert start <= paths.index("test-06") < end


def test_visible_selection_does_not_move_viewport():
    paths = (
        "ejtv",
        "enlace",
        "impact",
        "test-04",
        "test-05",
    )

    selection = IncomingSelectionState(
        selected_path_name="impact",
    )

    viewport = PanelViewport(
        offset=1,
        page_size=3,
    )

    updated = selection.ensure_visible(
        viewport,
        paths,
    )

    assert updated.offset == 1
    assert updated.page_size == 3
