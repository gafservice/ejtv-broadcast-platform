"""Contract tests for INCOMING contextual detail tab state."""

from dataclasses import FrozenInstanceError

import pytest

from app.dashboard.models.incoming_detail_tab_state import (
    IncomingDetailTab,
    IncomingDetailTabState,
)


def test_default_tab_is_signal():
    state = IncomingDetailTabState()

    assert state.active_tab is IncomingDetailTab.SIGNAL


def test_exactly_six_tabs_exist_in_contract_order():
    assert tuple(IncomingDetailTab) == (
        IncomingDetailTab.SIGNAL,
        IncomingDetailTab.TRANSPORT,
        IncomingDetailTab.VIDEO,
        IncomingDetailTab.AUDIO,
        IncomingDetailTab.EVENTS,
        IncomingDetailTab.STATISTICS,
    )


@pytest.mark.parametrize(
    "tab",
    list(IncomingDetailTab),
)
def test_can_select_every_contract_tab(tab):
    state = IncomingDetailTabState()

    updated = state.select(tab)

    assert updated.active_tab is tab


def test_selection_preserves_original_state():
    original = IncomingDetailTabState()

    updated = original.select(IncomingDetailTab.VIDEO)

    assert original.active_tab is IncomingDetailTab.SIGNAL
    assert updated.active_tab is IncomingDetailTab.VIDEO
    assert updated is not original


def test_state_is_immutable():
    state = IncomingDetailTabState()

    with pytest.raises(FrozenInstanceError):
        state.active_tab = IncomingDetailTab.AUDIO


def test_invalid_initial_tab_is_rejected():
    with pytest.raises(TypeError):
        IncomingDetailTabState(active_tab="video")


def test_invalid_selection_is_rejected():
    state = IncomingDetailTabState()

    with pytest.raises(TypeError):
        state.select("video")
