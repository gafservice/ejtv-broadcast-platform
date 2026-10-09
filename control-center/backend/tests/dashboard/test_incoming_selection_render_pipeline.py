"""Contract tests for INCOMING selection propagation."""

import inspect

from app.dashboard.application import DashboardApplication
from app.dashboard.renderers.dashboard_renderer import (
    DashboardRenderer,
)


def test_dashboard_renderer_accepts_incoming_selection_state():
    signature = inspect.signature(DashboardRenderer.render)

    assert "incoming_selection_state" in signature.parameters


def test_dashboard_application_passes_selection_to_renderer():
    source = inspect.getsource(DashboardApplication.run_once)

    assert "incoming_selection_state=" in source


def test_dashboard_renderer_forwards_selected_path_name():
    source = inspect.getsource(DashboardRenderer.render)

    assert "selected_path_name=" in source
