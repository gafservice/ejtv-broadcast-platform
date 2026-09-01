"""Aplicación de acciones de navegación sobre el estado del dashboard."""

from __future__ import annotations

from app.dashboard.models.dashboard_navigation_action import (
    DashboardNavigationAction,
)
from app.dashboard.models.dashboard_navigation_state import (
    DashboardNavigationState,
)


class DashboardNavigationController:
    """Transforma acciones abstractas en nuevo estado de navegación."""

    def apply(
        self,
        state: DashboardNavigationState,
        action: DashboardNavigationAction,
        *,
        total_items: int,
    ) -> DashboardNavigationState:
        if not isinstance(state, DashboardNavigationState):
            raise TypeError(
                "state must be a DashboardNavigationState"
            )

        if not isinstance(action, DashboardNavigationAction):
            raise TypeError(
                "action must be a DashboardNavigationAction"
            )

        if action is DashboardNavigationAction.NEXT_PANEL:
            return state.select_next()

        if action is DashboardNavigationAction.PREVIOUS_PANEL:
            return state.select_previous()

        if action is DashboardNavigationAction.SCROLL_UP:
            return state.move_active(
                -1,
                total_items=total_items,
            )

        if action is DashboardNavigationAction.SCROLL_DOWN:
            return state.move_active(
                1,
                total_items=total_items,
            )

        if action is DashboardNavigationAction.PAGE_UP:
            return state.page_up_active(
                total_items=total_items,
            )

        if action is DashboardNavigationAction.PAGE_DOWN:
            return state.page_down_active(
                total_items=total_items,
            )

        if action is DashboardNavigationAction.HOME:
            return state.home_active()

        if action is DashboardNavigationAction.END:
            return state.end_active(
                total_items=total_items,
            )

        if action is DashboardNavigationAction.QUIT:
            return state

        raise ValueError(
            f"Unsupported navigation action: {action}"
        )
