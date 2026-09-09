"""Tests del renderizador PLATFORM HEALTH."""

from datetime import UTC, datetime

from rich.console import Console
from rich.panel import Panel

from app.dashboard.models import PlatformHealthPanelData
from app.dashboard.renderers.platform_health_renderer import (
    PlatformHealthRenderer,
)


def render_to_text(panel: Panel) -> str:
    """Renderiza un Panel Rich como texto para inspección."""

    console = Console(
        width=80,
        record=True,
        force_terminal=False,
        color_system=None,
    )
    console.print(panel)
    return console.export_text()


def test_platform_health_renderer_renders_healthy_summary() -> None:
    """Debe representar sin recalcular el resumen agregado."""

    data = PlatformHealthPanelData(
        status="HEALTHY",
        worst_status="CRITICAL",
        healthy_count=2,
        degraded_count=1,
        critical_count=1,
        unknown_count=1,
        evidence_coverage=0.8,
        affected_fraction=0.5,
        service_count=3,
        captured_at=datetime(
            2026,
            9,
            9,
            21,
            45,
            tzinfo=UTC,
        ),
    )

    panel = PlatformHealthRenderer().render(data)
    output = render_to_text(panel)

    assert panel.title == "PLATFORM HEALTH"
    assert "Status: HEALTHY" in output
    assert "Worst: CRITICAL" in output
    assert "Services: 3" in output
    assert "Coverage: 80%" in output
    assert "Affected: 50%" in output
    assert "H:2 D:1 C:1 U:1" in output


def test_platform_health_renderer_renders_unknown_population() -> None:
    """Debe preservar ausencia de cobertura y afectación."""

    data = PlatformHealthPanelData(
        status="UNKNOWN",
        worst_status="UNKNOWN",
        healthy_count=0,
        degraded_count=0,
        critical_count=0,
        unknown_count=0,
        evidence_coverage=None,
        affected_fraction=None,
        service_count=0,
        captured_at=datetime(
            2026,
            9,
            9,
            21,
            46,
            tzinfo=UTC,
        ),
    )

    panel = PlatformHealthRenderer().render(data)
    output = render_to_text(panel)

    assert panel.title == "PLATFORM HEALTH"
    assert "Status: UNKNOWN" in output
    assert "Worst: UNKNOWN" in output
    assert "Services: 0" in output
    assert "Coverage: N/A" in output
    assert "Affected: N/A" in output
    assert "H:0 D:0 C:0 U:0" in output


def test_platform_health_renderer_renders_unavailable() -> None:
    """Debe representar ausencia del modelo sin inventar salud."""

    panel = PlatformHealthRenderer().render(None)
    output = render_to_text(panel)

    assert panel.title == "PLATFORM HEALTH"
    assert "Status: UNKNOWN" in output
    assert "Worst: UNKNOWN" in output
    assert "Services: 0" in output
    assert "Coverage: N/A" in output
    assert "Affected: N/A" in output
    assert "H:0 D:0 C:0 U:0" in output
