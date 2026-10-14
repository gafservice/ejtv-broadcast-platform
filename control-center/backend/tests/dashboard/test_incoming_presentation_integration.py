"""Contract: presentation mode propagates to INCOMING renderer."""

from inspect import signature

from app.dashboard.renderers.dashboard_renderer import (
    DashboardRenderer,
)


def test_dashboard_renderer_accepts_presentation_mode():
    parameters = signature(
        DashboardRenderer.render
    ).parameters

    assert "incoming_presentation_mode" in parameters

    parameter = parameters["incoming_presentation_mode"]

    assert parameter.default == "full"


def test_dashboard_renderer_forwards_compact_mode():
    import inspect

    source = inspect.getsource(
        DashboardRenderer.render
    )

    assert "incoming_presentation_mode" in source

    assert "presentation_mode=incoming_presentation_mode" in source


def test_dashboard_renderer_preserves_full_mode_default():
    parameters = signature(
        DashboardRenderer.render
    ).parameters

    assert (
        parameters["incoming_presentation_mode"].default
        == "full"
    )
