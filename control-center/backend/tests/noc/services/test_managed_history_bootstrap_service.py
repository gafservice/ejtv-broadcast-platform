from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.historical_range_repository import (
    HistoricalRangeRepository,
)
from app.noc.history.managed_history_repository import (
    ManagedHistoryRepository,
)
from app.noc.services.managed_history_bootstrap_service import (
    ManagedHistoryBootstrapService,
)


NODE = NodeId(
    "node-001",
    "node-001",
    "Node 001",
    datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    ),
)

INSTANCE = NodeInstanceId("instance-001")

NOW = datetime(
    2026,
    9,
    4,
    1,
    30,
    tzinfo=timezone.utc,
)


def make_service(
    *,
    existing=None,
    first_timestamp=None,
):
    managed = Mock(
        spec=ManagedHistoryRepository
    )
    historical = Mock(
        spec=HistoricalRangeRepository
    )

    managed.get_managed_since_day.return_value = (
        existing
    )

    managed.ensure_managed_since_day.side_effect = (
        lambda **kwargs: kwargs["day"]
    )

    historical.first_historical_timestamp.return_value = (
        first_timestamp
    )

    service = ManagedHistoryBootstrapService(
        managed_history_repository=managed,
        historical_range_repository=historical,
        clock=lambda: NOW,
    )

    return service, managed, historical


def test_existing_anchor_is_authoritative() -> None:
    existing = date(
        2026,
        9,
        2,
    )

    service, managed, historical = make_service(
        existing=existing,
    )

    result = service.ensure_anchor(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    assert result == existing

    historical.first_historical_timestamp.assert_not_called()
    managed.ensure_managed_since_day.assert_not_called()


def test_existing_history_bootstraps_from_earliest_timestamp() -> None:
    first_timestamp = datetime(
        2026,
        9,
        2,
        6,
        40,
        tzinfo=timezone.utc,
    )

    service, managed, historical = make_service(
        first_timestamp=first_timestamp,
    )

    result = service.ensure_anchor(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    assert result == date(
        2026,
        9,
        2,
    )

    historical.first_historical_timestamp.assert_called_once_with(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    managed.ensure_managed_since_day.assert_called_once_with(
        node_id=NODE,
        instance_id=INSTANCE,
        day=date(2026, 9, 2),
        created_at=NOW,
    )


def test_empty_history_bootstraps_from_current_utc_day() -> None:
    service, managed, historical = make_service()

    result = service.ensure_anchor(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    assert result == date(
        2026,
        9,
        4,
    )

    managed.ensure_managed_since_day.assert_called_once_with(
        node_id=NODE,
        instance_id=INSTANCE,
        day=date(2026, 9, 4),
        created_at=NOW,
    )


def test_bootstrap_normalizes_clock_to_utc() -> None:
    managed = Mock(
        spec=ManagedHistoryRepository
    )
    historical = Mock(
        spec=HistoricalRangeRepository
    )

    managed.get_managed_since_day.return_value = None
    managed.ensure_managed_since_day.side_effect = (
        lambda **kwargs: kwargs["day"]
    )
    historical.first_historical_timestamp.return_value = None

    local_time = datetime(
        2026,
        9,
        3,
        20,
        30,
        tzinfo=timezone(
            -timedelta(hours=6)
        ),
    )

    service = ManagedHistoryBootstrapService(
        managed_history_repository=managed,
        historical_range_repository=historical,
        clock=lambda: local_time,
    )

    result = service.ensure_anchor(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    assert result == date(
        2026,
        9,
        4,
    )

    managed.ensure_managed_since_day.assert_called_once_with(
        node_id=NODE,
        instance_id=INSTANCE,
        day=date(2026, 9, 4),
        created_at=datetime(
            2026,
            9,
            4,
            2,
            30,
            tzinfo=timezone.utc,
        ),
    )


def test_historical_timestamp_is_normalized_to_utc_day() -> None:
    first_timestamp = datetime(
        2026,
        9,
        1,
        20,
        30,
        tzinfo=timezone(
            -timedelta(hours=6)
        ),
    )

    service, managed, _ = make_service(
        first_timestamp=first_timestamp,
    )

    result = service.ensure_anchor(
        node_id=NODE,
        instance_id=INSTANCE,
    )

    assert result == date(
        2026,
        9,
        2,
    )

    managed.ensure_managed_since_day.assert_called_once_with(
        node_id=NODE,
        instance_id=INSTANCE,
        day=date(2026, 9, 2),
        created_at=NOW,
    )
