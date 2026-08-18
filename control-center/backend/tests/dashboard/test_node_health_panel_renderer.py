"""Tests del renderizador NODE HEALTH."""

from datetime import UTC, datetime

from rich.panel import Panel

from app.dashboard.models import (
    NodeHealthInterfaceRowData,
    NodeHealthPanelData,
)
from app.dashboard.renderers.node_health_panel_renderer import (
    NodeHealthPanelRenderer,
)


CAPTURED_AT = datetime(
    2026,
    8,
    18,
    23,
    59,
    tzinfo=UTC,
)


def test_render_healthy_node_health() -> None:
    renderer = NodeHealthPanelRenderer()

    data = NodeHealthPanelData(
        state="HEALTHY",
        system_state="HEALTHY",
        network_state="HEALTHY",
        interfaces=(),
        captured_at=CAPTURED_AT,
    )

    panel = renderer.render(data)

    assert isinstance(panel, Panel)
    assert panel.title == "NODE HEALTH"
    assert panel.border_style == "green"

    text = panel.renderable.plain

    assert "Status: HEALTHY" in text
    assert "System: HEALTHY" in text
    assert "Network: HEALTHY" in text
    assert "Issues: 0" in text


def test_render_critical_node_health() -> None:
    renderer = NodeHealthPanelRenderer()

    data = NodeHealthPanelData(
        state="CRITICAL",
        system_state="HEALTHY",
        network_state="CRITICAL",
        interfaces=(
            NodeHealthInterfaceRowData(
                interface="ens2f0",
                state="CRITICAL",
                reason=(
                    "Required critical interface "
                    "is not operational"
                ),
            ),
        ),
        captured_at=CAPTURED_AT,
    )

    panel = renderer.render(data)

    assert panel.title == "NODE HEALTH"
    assert panel.border_style == "red"

    text = panel.renderable.plain

    assert "Status: CRITICAL" in text
    assert "System: HEALTHY" in text
    assert "Network: CRITICAL" in text
    assert "Issues: 1" in text
    assert "ens2f0: CRITICAL" in text


def test_render_unavailable_node_health() -> None:
    renderer = NodeHealthPanelRenderer()

    panel = renderer.render(None)

    assert panel.title == "NODE HEALTH"
    assert panel.border_style == "blue"

    text = panel.renderable.plain

    assert "Status: UNKNOWN" in text
    assert "System: UNKNOWN" in text
    assert "Network: UNKNOWN" in text
    assert "Issues: 0" in text


def test_healthy_interfaces_are_not_counted_as_issues() -> None:
    renderer = NodeHealthPanelRenderer()

    data = NodeHealthPanelData(
        state="HEALTHY",
        system_state="HEALTHY",
        network_state="HEALTHY",
        interfaces=(
            NodeHealthInterfaceRowData(
                interface="enp9s0",
                state="HEALTHY",
                reason="Interface is operational",
            ),
            NodeHealthInterfaceRowData(
                interface="ens2f0",
                state="HEALTHY",
                reason="Interface is operational",
            ),
            NodeHealthInterfaceRowData(
                interface="ens2f1",
                state="HEALTHY",
                reason="Optional interface is not required",
            ),
        ),
        captured_at=CAPTURED_AT,
    )

    panel = renderer.render(data)
    text = panel.renderable.plain

    assert "Issues: 0" in text
    assert "enp9s0:" not in text
    assert "ens2f0:" not in text
    assert "ens2f1:" not in text


def test_only_unhealthy_interfaces_are_counted_as_issues() -> None:
    renderer = NodeHealthPanelRenderer()

    data = NodeHealthPanelData(
        state="WARNING",
        system_state="HEALTHY",
        network_state="WARNING",
        interfaces=(
            NodeHealthInterfaceRowData(
                interface="enp9s0",
                state="HEALTHY",
                reason="Interface is operational",
            ),
            NodeHealthInterfaceRowData(
                interface="ens2f0",
                state="WARNING",
                reason="Elevated network error or drop rate",
            ),
            NodeHealthInterfaceRowData(
                interface="ens2f1",
                state="HEALTHY",
                reason="Optional interface is not required",
            ),
        ),
        captured_at=CAPTURED_AT,
    )

    panel = renderer.render(data)
    text = panel.renderable.plain

    assert "Issues: 1" in text
    assert "ens2f0: WARNING" in text
    assert "enp9s0:" not in text
