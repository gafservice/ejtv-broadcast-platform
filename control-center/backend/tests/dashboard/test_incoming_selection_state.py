"""ENG-013C 235E.25 — INCOMING selection contract."""

from dataclasses import FrozenInstanceError

import pytest

from app.dashboard.models.incoming_selection_state import (
    IncomingSelectionState,
)


def test_selection_defaults_to_none():
    state = IncomingSelectionState()

    assert state.selected_path_name is None


def test_first_reconciliation_selects_first_available_path():
    state = IncomingSelectionState()

    updated = state.reconcile(("service-a", "service-b"))

    assert updated.selected_path_name == "service-a"


def test_empty_collection_clears_selection():
    state = IncomingSelectionState(
        selected_path_name="service-a"
    )

    updated = state.reconcile(())

    assert updated.selected_path_name is None


def test_selection_survives_row_reordering():
    state = IncomingSelectionState(
        selected_path_name="service-b"
    )

    updated = state.reconcile(
        ("service-c", "service-b", "service-a")
    )

    assert updated.selected_path_name == "service-b"


def test_missing_selected_path_falls_back_to_first():
    state = IncomingSelectionState(
        selected_path_name="service-b"
    )

    updated = state.reconcile(
        ("service-c", "service-a")
    )

    assert updated.selected_path_name == "service-c"


def test_removed_selection_is_not_restored_automatically():
    state = IncomingSelectionState(
        selected_path_name="service-b"
    )

    updated = state.reconcile(("service-a",))
    restored = updated.reconcile(
        ("service-a", "service-b")
    )

    assert updated.selected_path_name == "service-a"
    assert restored.selected_path_name == "service-a"


def test_move_next_uses_current_row_order():
    state = IncomingSelectionState(
        selected_path_name="service-b"
    )

    updated = state.move(
        1,
        ("service-c", "service-b", "service-a"),
    )

    assert updated.selected_path_name == "service-a"


def test_move_previous_uses_current_row_order():
    state = IncomingSelectionState(
        selected_path_name="service-b"
    )

    updated = state.move(
        -1,
        ("service-c", "service-b", "service-a"),
    )

    assert updated.selected_path_name == "service-c"


def test_move_does_not_wrap_at_boundaries():
    first = IncomingSelectionState(
        selected_path_name="service-a"
    )
    last = IncomingSelectionState(
        selected_path_name="service-c"
    )

    assert first.move(
        -1,
        ("service-a", "service-b", "service-c"),
    ).selected_path_name == "service-a"

    assert last.move(
        1,
        ("service-a", "service-b", "service-c"),
    ).selected_path_name == "service-c"


def test_home_and_end_select_boundaries():
    paths = ("service-c", "service-a", "service-b")

    state = IncomingSelectionState(
        selected_path_name="service-a"
    )

    assert state.home(paths).selected_path_name == "service-c"
    assert state.end(paths).selected_path_name == "service-b"


def test_state_is_immutable():
    state = IncomingSelectionState(
        selected_path_name="service-a"
    )

    with pytest.raises(FrozenInstanceError):
        state.selected_path_name = "service-b"


def test_reconciliation_does_not_mutate_original():
    state = IncomingSelectionState(
        selected_path_name="service-b"
    )

    updated = state.reconcile(("service-a",))

    assert state.selected_path_name == "service-b"
    assert updated.selected_path_name == "service-a"


@pytest.mark.parametrize(
    "invalid",
    (
        123,
        "",
        False,
    ),
)
def test_rejects_invalid_selected_identity(invalid):
    with pytest.raises((TypeError, ValueError)):
        IncomingSelectionState(
            selected_path_name=invalid
        )
