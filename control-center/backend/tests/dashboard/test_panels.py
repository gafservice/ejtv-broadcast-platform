"""Pruebas de los paneles principales del monitor NOC."""

from rich.panel import Panel

from app.dashboard.panels.footer import build_footer_panel
from app.dashboard.panels.header import build_header_panel
from app.dashboard.panels.server import build_server_panel
from app.dashboard.panels.streaming import build_streaming_panel
from app.dashboard.panels.system import build_system_panel


def test_build_header_panel_returns_panel() -> None:
    panel = build_header_panel()

    assert isinstance(panel, Panel)


def test_build_server_panel_returns_panel() -> None:
    panel = build_server_panel()

    assert isinstance(panel, Panel)


def test_build_streaming_panel_returns_panel() -> None:
    panel = build_streaming_panel()

    assert isinstance(panel, Panel)


def test_build_system_panel_returns_panel() -> None:
    panel = build_system_panel()

    assert isinstance(panel, Panel)


def test_build_footer_panel_returns_panel() -> None:
    panel = build_footer_panel()

    assert isinstance(panel, Panel)
