"""Tests del renderer ACTIVE ALARMS."""

from datetime import UTC, datetime

import pytest
from rich.panel import Panel

from app.dashboard.models import (
    ActiveAlarmRowData,
    ActiveAlarmsPanelData,
)
from app.dashboard.renderers.active_alarms_panel_renderer import (
    ActiveAlarmsPanelRenderer,
)


OPENED_AT = datetime(
    2026,
    8,
    21,
    23,
    30,
    15,
    tzinfo=UTC,
)


def make_alarm(
    *,
    alarm_id: str = "alarm-001",
    severity: str = "CRITICAL",
    state: str = "ACTIVE",
) -> ActiveAlarmRowData:
    return ActiveAlarmRowData(
        alarm_id=alarm_id,
        alarm_type="NODE_HEALTH_DEGRADED",
        severity=severity,
        state=state,
        message="Node health degraded to CRITICAL",
        opened_at=OPENED_AT,
    )


def test_render_returns_panel() -> None:
    renderer = ActiveAlarmsPanelRenderer()

    panel = renderer.render(
        ActiveAlarmsPanelData(
            alarms=(),
        )
    )

    assert isinstance(
        panel,
        Panel,
    )


def test_render_uses_active_alarms_title() -> None:
    renderer = ActiveAlarmsPanelRenderer()

    panel = renderer.render(
        ActiveAlarmsPanelData(
            alarms=(),
        )
    )

    assert panel.title == "ACTIVE ALARMS"


def test_render_empty_panel() -> None:
    renderer = ActiveAlarmsPanelRenderer()

    panel = renderer.render(
        ActiveAlarmsPanelData(
            alarms=(),
        )
    )

    text = panel.renderable

    assert text.row_count == 1


def test_render_active_alarm() -> None:
    renderer = ActiveAlarmsPanelRenderer()

    panel = renderer.render(
        ActiveAlarmsPanelData(
            alarms=(
                make_alarm(),
            ),
        )
    )

    table = panel.renderable

    assert table.row_count == 1


def test_format_time() -> None:
    renderer = ActiveAlarmsPanelRenderer()

    assert renderer._format_time(
        make_alarm()
    ) == "23:30:15"


@pytest.mark.parametrize(
    "severity",
    (
        "INFO",
        "WARNING",
        "MINOR",
        "MAJOR",
        "CRITICAL",
    ),
)
def test_format_severity(
    severity: str,
) -> None:
    renderer = ActiveAlarmsPanelRenderer()

    text = renderer._format_severity(
        make_alarm(
            severity=severity,
        )
    )

    assert text.plain == severity


@pytest.mark.parametrize(
    "state",
    (
        "ACTIVE",
        "ACKNOWLEDGED",
    ),
)
def test_format_state(
    state: str,
) -> None:
    renderer = ActiveAlarmsPanelRenderer()

    text = renderer._format_state(
        make_alarm(
            state=state,
        )
    )

    assert text.plain == state


def test_render_requires_panel_data() -> None:
    renderer = ActiveAlarmsPanelRenderer()

    with pytest.raises(TypeError):
        renderer.render(
            object()  # type: ignore[arg-type]
        )
