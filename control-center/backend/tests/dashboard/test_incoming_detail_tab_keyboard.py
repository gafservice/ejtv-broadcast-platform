"""Contract tests for INCOMING detail tab keyboard navigation."""

import pytest

from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.services.dashboard_key_parser import (
    DashboardKeyParser,
)


@pytest.mark.parametrize(
    ("sequence", "action_name"),
    (
        (b"1", "SELECT_SIGNAL_TAB"),
        (b"2", "SELECT_TRANSPORT_TAB"),
        (b"3", "SELECT_VIDEO_TAB"),
        (b"4", "SELECT_AUDIO_TAB"),
        (b"5", "SELECT_EVENTS_TAB"),
        (b"6", "SELECT_STATISTICS_TAB"),
    ),
)
def test_numeric_keys_map_to_detail_tabs(
    sequence,
    action_name,
):
    parser = DashboardKeyParser()

    expected = getattr(DashboardNavigationAction, action_name)

    assert parser.parse(sequence) is expected


@pytest.mark.parametrize(
    "sequence",
    (
        b"0",
        b"7",
        b"8",
        b"9",
    ),
)
def test_unassigned_numeric_keys_are_ignored(sequence):
    parser = DashboardKeyParser()

    assert parser.parse(sequence) is None


@pytest.mark.parametrize(
    ("sequence", "expected"),
    (
        (b"\t", DashboardNavigationAction.NEXT_PANEL),
        (b"\x1b[Z", DashboardNavigationAction.PREVIOUS_PANEL),
        (b"\x1b[A", DashboardNavigationAction.SCROLL_UP),
        (b"\x1b[B", DashboardNavigationAction.SCROLL_DOWN),
        (b"\x1b[C", DashboardNavigationAction.NEXT_VIEW),
        (b"\x1b[D", DashboardNavigationAction.PREVIOUS_VIEW),
        (b"\x1b[H", DashboardNavigationAction.HOME),
        (b"\x1b[F", DashboardNavigationAction.END),
        (b"q", DashboardNavigationAction.QUIT),
        (b"Q", DashboardNavigationAction.QUIT),
    ),
)
def test_existing_navigation_bindings_are_preserved(
    sequence,
    expected,
):
    parser = DashboardKeyParser()

    assert parser.parse(sequence) is expected
