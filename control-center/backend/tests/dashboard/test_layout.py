"""Pruebas del layout principal del monitor NOC."""

from io import StringIO

from rich.console import Console
from rich.layout import Layout

from app.dashboard.layout import build_dashboard


def render_to_text(layout: Layout) -> str:
    """Renderiza un layout Rich como texto para inspeccionarlo."""

    output = StringIO()

    console = Console(
        file=output,
        force_terminal=False,
        color_system=None,
        width=140,
        height=40,
    )

    console.print(layout)

    return output.getvalue()


def test_build_dashboard_returns_rich_layout() -> None:
    """El constructor debe producir un Layout de Rich."""

    dashboard = build_dashboard()

    assert isinstance(dashboard, Layout)


def test_dashboard_contains_main_identity() -> None:
    """La pantalla debe identificar claramente el centro de operaciones."""

    dashboard = build_dashboard()
    rendered = render_to_text(dashboard)

    assert "CONTROL CENTER" in rendered
    assert "NETWORK OPERATIONS CENTER" in rendered
    assert "Live Operations Monitor" in rendered


def test_dashboard_contains_main_sections() -> None:
    """El layout debe incluir las secciones operativas principales."""

    dashboard = build_dashboard()
    rendered = render_to_text(dashboard)

    assert "SERVER" in rendered
    assert "STREAMING" in rendered
    assert "SYSTEM" in rendered
    assert "ACTIVE STREAMS" in rendered


def test_dashboard_indicates_disconnected_data() -> None:
    """La versión inicial debe indicar que los datos aún no están conectados."""

    dashboard = build_dashboard()
    rendered = render_to_text(dashboard)

    assert "Datos aún no conectados" in rendered


def test_dashboard_contains_mission_identifier() -> None:
    """El pie debe identificar la misión en desarrollo."""

    dashboard = build_dashboard()
    rendered = render_to_text(dashboard)

    assert "MISSION-021" in rendered
