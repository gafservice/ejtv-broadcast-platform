"""Pruebas de los totales de navegación del dashboard."""

import pytest

from app.dashboard.models.dashboard_navigation_state import (
    NavigablePanel,
)
from app.dashboard.models.dashboard_navigation_totals import (
    DashboardNavigationTotals,
)


def test_defaults_are_zero() -> None:
    totals = DashboardNavigationTotals()

    assert totals.active_connections == 0
    assert totals.active_alarms == 0
    assert totals.recent_events == 0


def test_returns_total_for_each_panel() -> None:
    totals = DashboardNavigationTotals(
        active_connections=11,
        active_alarms=7,
        recent_events=23,
    )

    assert totals.for_panel(
        NavigablePanel.ACTIVE_CONNECTIONS
    ) == 11

    assert totals.for_panel(
        NavigablePanel.ACTIVE_ALARMS
    ) == 7

    assert totals.for_panel(
        NavigablePanel.RECENT_EVENTS
    ) == 23


@pytest.mark.parametrize(
    "kwargs",
    (
        {"active_connections": -1},
        {"active_alarms": -1},
        {"recent_events": -1},
    ),
)
def test_rejects_negative_totals(kwargs) -> None:
    with pytest.raises(
        ValueError,
        match="greater than or equal to zero",
    ):
        DashboardNavigationTotals(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    (
        {"active_connections": True},
        {"active_alarms": 1.5},
        {"recent_events": "3"},
    ),
)
def test_rejects_invalid_total_types(kwargs) -> None:
    with pytest.raises(
        TypeError,
        match="must be an int",
    ):
        DashboardNavigationTotals(**kwargs)


def test_rejects_invalid_panel() -> None:
    totals = DashboardNavigationTotals()

    with pytest.raises(
        TypeError,
        match="panel must be a NavigablePanel",
    ):
        totals.for_panel("active_connections")
