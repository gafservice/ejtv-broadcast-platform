"""Pruebas del renderizador de salud del streaming."""

from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel

from app.dashboard.renderers.streaming_health_renderer import (
    StreamingHealthRenderer,
)
from app.domain.streaming import HealthStatus, StreamingHealth


CAPTURED_AT = datetime(
    2026,
    7,
    22,
    20,
    30,
    tzinfo=timezone.utc,
)


def build_streaming_health() -> StreamingHealth:
    """Construye un estado de salud válido para las pruebas."""

    return StreamingHealth(
        captured_at=CAPTURED_AT,
        paths=(),
        status=HealthStatus.HEALTHY,
        message="El subsistema SRT funciona correctamente.",
    )


def render_to_text(panel: Panel) -> str:
    """Convierte un panel Rich en texto verificable."""

    console = Console(
        record=True,
        width=120,
        color_system=None,
    )
    console.print(panel)

    return console.export_text()


def test_streaming_health_renderer_can_be_created() -> None:
    renderer = StreamingHealthRenderer()

    assert renderer is not None


def test_render_returns_rich_panel() -> None:
    renderer = StreamingHealthRenderer()

    result = renderer.render(build_streaming_health())

    assert isinstance(result, Panel)


def test_render_contains_health_summary() -> None:
    renderer = StreamingHealthRenderer()

    panel = renderer.render(build_streaming_health())
    output = render_to_text(panel)

    assert "STREAM HEALTH" in output
    assert "Status" in output
    assert "HEALTHY" in output
    assert "Paths" in output
    assert "0" in output
    assert "Connections" in output
    assert "Captured" in output
    assert "2026-07-22 20:30:00 UTC" in output
    assert "Summary" in output
    assert "El subsistema SRT funciona" in output
    assert "correctamente." not in output


def test_render_accepts_missing_health() -> None:
    renderer = StreamingHealthRenderer()

    panel = renderer.render(None)
    output = render_to_text(panel)

    assert isinstance(panel, Panel)
    assert "STREAM HEALTH" in output
    assert "UNKNOWN" in output
    assert "No health data available." in output
    assert "Summary: No health data available." in output
