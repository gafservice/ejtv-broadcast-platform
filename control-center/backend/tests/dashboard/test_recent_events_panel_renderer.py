"""Tests del renderizador RECENT EVENTS."""

from datetime import UTC, datetime

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.dashboard.models import (
    RecentEventRowData,
    RecentEventsPanelData,
)
from app.dashboard.renderers.recent_events_panel_renderer import (
    RecentEventsPanelRenderer,
)


def make_event(
    *,
    event_id: str = "event-001",
    event_type: str = "NODE_HEALTH_DEGRADED",
    severity: str = "WARNING",
    title: str = "Node health degraded",
    hour: int = 18,
    minute: int = 30,
    second: int = 15,
) -> RecentEventRowData:
    """Construye un evento determinista para las pruebas."""

    return RecentEventRowData(
        event_id=event_id,
        event_type=event_type,
        severity=severity,
        title=title,
        occurred_at=datetime(
            2026,
            8,
            20,
            hour,
            minute,
            second,
            tzinfo=UTC,
        ),
    )


def test_render_recent_events_panel() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(
            make_event(),
        ),
    )

    panel = renderer.render(data)

    assert isinstance(panel, Panel)
    assert panel.title == "RECENT EVENTS"
    assert isinstance(panel.renderable, Table)

    table = panel.renderable

    assert table.row_count == 1


def test_render_contains_event_values() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(
            make_event(),
        ),
    )

    panel = renderer.render(data)
    table = panel.renderable

    row = table.rows[0]

    cells = tuple(
        column._cells[0]
        for column in table.columns
    )

    assert cells[0] == "18:30:15"

    assert isinstance(
        cells[1],
        Text,
    )
    assert cells[1].plain == "WARNING"

    assert cells[2] == "NODE_HEALTH_DEGRADED"
    assert cells[3] == "Node health degraded"

    assert row is not None


def test_warning_severity_uses_warning_style() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(
            make_event(
                severity="WARNING",
            ),
        ),
    )

    panel = renderer.render(data)

    severity = panel.renderable.columns[1]._cells[0]

    assert isinstance(
        severity,
        Text,
    )
    assert severity.plain == "WARNING"
    assert severity.style == "bold yellow"


def test_critical_severity_uses_critical_style() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(
            make_event(
                severity="CRITICAL",
            ),
        ),
    )

    panel = renderer.render(data)

    severity = panel.renderable.columns[1]._cells[0]

    assert isinstance(
        severity,
        Text,
    )
    assert severity.plain == "CRITICAL"
    assert severity.style == "bold red"


def test_info_severity_uses_info_style() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(
            make_event(
                severity="INFO",
            ),
        ),
    )

    panel = renderer.render(data)

    severity = panel.renderable.columns[1]._cells[0]

    assert isinstance(
        severity,
        Text,
    )
    assert severity.plain == "INFO"
    assert severity.style == "green"


def test_unknown_severity_uses_fallback_style() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(
            make_event(
                severity="CUSTOM",
            ),
        ),
    )

    panel = renderer.render(data)

    severity = panel.renderable.columns[1]._cells[0]

    assert isinstance(
        severity,
        Text,
    )
    assert severity.plain == "CUSTOM"
    assert severity.style == "bold dim"


def test_render_empty_recent_events() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(),
    )

    panel = renderer.render(data)

    assert panel.title == "RECENT EVENTS"

    table = panel.renderable

    assert isinstance(
        table,
        Table,
    )
    assert table.row_count == 1

    title_cell = table.columns[3]._cells[0]

    assert isinstance(
        title_cell,
        Text,
    )
    assert title_cell.plain == "No recent events"
    assert title_cell.style == "dim"


def test_renderer_preserves_event_order() -> None:
    renderer = RecentEventsPanelRenderer()

    data = RecentEventsPanelData(
        events=(
            make_event(
                event_id="event-002",
                event_type="NODE_HEALTH_RECOVERED",
                severity="INFO",
                title="Node health recovered",
                hour=19,
            ),
            make_event(
                event_id="event-001",
                event_type="NODE_HEALTH_DEGRADED",
                severity="WARNING",
                title="Node health degraded",
                hour=18,
            ),
        ),
    )

    panel = renderer.render(data)
    table = panel.renderable

    assert table.row_count == 2

    assert (
        table.columns[2]._cells[0]
        == "NODE_HEALTH_RECOVERED"
    )
    assert (
        table.columns[2]._cells[1]
        == "NODE_HEALTH_DEGRADED"
    )


def test_format_time_is_compact() -> None:
    event = make_event(
        hour=7,
        minute=5,
        second=9,
    )

    value = (
        RecentEventsPanelRenderer
        ._format_time(event)
    )

    assert value == "07:05:09"
