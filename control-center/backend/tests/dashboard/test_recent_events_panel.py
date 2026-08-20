"""Tests para los modelos del panel RECENT EVENTS."""

from datetime import datetime, timezone

import pytest

from app.dashboard.models.recent_events_panel import (
    RecentEventRowData,
    RecentEventsPanelData,
)


OCCURRED_AT = datetime(
    2026,
    8,
    20,
    20,
    0,
    tzinfo=timezone.utc,
)


def make_event(
    *,
    event_id: str = "event-001",
) -> RecentEventRowData:
    return RecentEventRowData(
        event_id=event_id,
        event_type="NODE_HEALTH_DEGRADED",
        severity="WARNING",
        title="Node health degraded",
        occurred_at=OCCURRED_AT,
    )


def test_recent_event_row_accepts_valid_data() -> None:
    event = make_event()

    assert event.event_id == "event-001"
    assert event.event_type == "NODE_HEALTH_DEGRADED"
    assert event.severity == "WARNING"
    assert event.title == "Node health degraded"
    assert event.occurred_at == OCCURRED_AT


def test_recent_event_row_normalizes_text() -> None:
    event = RecentEventRowData(
        event_id="  event-001  ",
        event_type="  NODE_HEALTH_DEGRADED  ",
        severity="  WARNING  ",
        title="  Node health degraded  ",
        occurred_at=OCCURRED_AT,
    )

    assert event.event_id == "event-001"
    assert event.event_type == "NODE_HEALTH_DEGRADED"
    assert event.severity == "WARNING"
    assert event.title == "Node health degraded"


@pytest.mark.parametrize(
    "field_name",
    (
        "event_id",
        "event_type",
        "severity",
        "title",
    ),
)
def test_recent_event_row_rejects_empty_text(
    field_name: str,
) -> None:
    kwargs = {
        "event_id": "event-001",
        "event_type": "NODE_HEALTH_DEGRADED",
        "severity": "WARNING",
        "title": "Node health degraded",
        "occurred_at": OCCURRED_AT,
    }

    kwargs[field_name] = "   "

    with pytest.raises(ValueError):
        RecentEventRowData(**kwargs)


def test_recent_event_row_rejects_invalid_datetime() -> None:
    with pytest.raises(ValueError):
        RecentEventRowData(
            event_id="event-001",
            event_type="NODE_HEALTH_DEGRADED",
            severity="WARNING",
            title="Node health degraded",
            occurred_at=object(),  # type: ignore[arg-type]
        )


def test_recent_event_row_requires_timezone() -> None:
    with pytest.raises(ValueError):
        RecentEventRowData(
            event_id="event-001",
            event_type="NODE_HEALTH_DEGRADED",
            severity="WARNING",
            title="Node health degraded",
            occurred_at=datetime(
                2026,
                8,
                20,
                20,
                0,
            ),
        )


def test_recent_events_panel_accepts_empty_tuple() -> None:
    panel = RecentEventsPanelData(
        events=(),
    )

    assert panel.events == ()
    assert panel.event_count == 0
    assert panel.is_empty is True


def test_recent_events_panel_accepts_events() -> None:
    panel = RecentEventsPanelData(
        events=(
            make_event(
                event_id="event-001"
            ),
            make_event(
                event_id="event-002"
            ),
        )
    )

    assert panel.event_count == 2
    assert panel.is_empty is False


def test_recent_events_panel_requires_tuple() -> None:
    with pytest.raises(ValueError):
        RecentEventsPanelData(
            events=[],  # type: ignore[arg-type]
        )


def test_recent_events_panel_rejects_invalid_entries() -> None:
    with pytest.raises(ValueError):
        RecentEventsPanelData(
            events=(
                object(),  # type: ignore[arg-type]
            )
        )


def test_recent_events_panel_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError):
        RecentEventsPanelData(
            events=(
                make_event(
                    event_id="event-001"
                ),
                make_event(
                    event_id="event-001"
                ),
            )
        )
