"""Contract tests for SQLite Signal Health current state.

ENG-013C — Signal Health Current State

These tests define persistence semantics only.

The repository:
- stores the latest canonical Signal Health state;
- isolates state by profile/service/path identity;
- survives repository reconstruction;
- allows newer or equal observations to replace current state;
- rejects temporal rollback by preserving the newer observation.

Schema ownership remains with SQLiteHistoryDatabase.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.current_state.signal_health_current_state import (
    SignalHealthCurrentState,
    SignalHealthCurrentStateRepository,
)
from app.noc.current_state.sqlite_signal_health_current_state_repository import (
    SQLiteSignalHealthCurrentStateRepository,
)
from app.noc.history.sqlite_database import SQLiteHistoryDatabase


BASE_TIME = datetime(
    2026,
    10,
    6,
    12,
    0,
    tzinfo=timezone.utc,
)


def _repository(
    tmp_path,
) -> SQLiteSignalHealthCurrentStateRepository:
    database = SQLiteHistoryDatabase(
        tmp_path / "noc-history.db"
    )
    database.initialize()

    return SQLiteSignalHealthCurrentStateRepository(
        database
    )


def _state(
    *,
    profile_id: str = "impact-main",
    service_id: str = "impact",
    path_name: str = "impact",
    observed_at: datetime = BASE_TIME,
    status: HealthStatus = HealthStatus.HEALTHY,
) -> SignalHealthCurrentState:
    health = SignalHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        media_status=status,
        transport_status=status,
        status=status,
    )

    return SignalHealthCurrentState(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        observed_at=observed_at,
        health=health,
    )


def test_repository_satisfies_current_state_port(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    assert isinstance(
        repository,
        SignalHealthCurrentStateRepository,
    )


def test_latest_returns_none_when_identity_is_unknown(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    assert repository.latest(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    ) is None


def test_saved_state_can_be_loaded(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)
    state = _state()

    repository.save(state=state)

    assert repository.latest(
        profile_id=state.profile_id,
        service_id=state.service_id,
        path_name=state.path_name,
    ) == state


def test_state_survives_repository_reconstruction(
    tmp_path,
) -> None:
    database_path = tmp_path / "noc-history.db"

    first_database = SQLiteHistoryDatabase(
        database_path
    )
    first_database.initialize()

    first_repository = (
        SQLiteSignalHealthCurrentStateRepository(
            first_database
        )
    )

    state = _state(
        status=HealthStatus.DEGRADED,
    )
    first_repository.save(state=state)

    second_database = SQLiteHistoryDatabase(
        database_path
    )
    second_database.initialize()

    second_repository = (
        SQLiteSignalHealthCurrentStateRepository(
            second_database
        )
    )

    assert second_repository.latest(
        profile_id=state.profile_id,
        service_id=state.service_id,
        path_name=state.path_name,
    ) == state


def test_newer_state_replaces_older_state(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    older = _state(
        observed_at=BASE_TIME,
        status=HealthStatus.HEALTHY,
    )
    newer = _state(
        observed_at=BASE_TIME + timedelta(seconds=5),
        status=HealthStatus.DEGRADED,
    )

    repository.save(state=older)
    repository.save(state=newer)

    assert repository.latest(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    ) == newer


def test_older_state_cannot_replace_newer_state(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    newer = _state(
        observed_at=BASE_TIME + timedelta(seconds=5),
        status=HealthStatus.CRITICAL,
    )
    older = _state(
        observed_at=BASE_TIME,
        status=HealthStatus.HEALTHY,
    )

    repository.save(state=newer)
    repository.save(state=older)

    assert repository.latest(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    ) == newer


def test_equal_timestamp_can_replace_current_state(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    first = _state(
        observed_at=BASE_TIME,
        status=HealthStatus.HEALTHY,
    )
    replacement = _state(
        observed_at=BASE_TIME,
        status=HealthStatus.DEGRADED,
    )

    repository.save(state=first)
    repository.save(state=replacement)

    assert repository.latest(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    ) == replacement


def test_state_is_isolated_by_full_signal_identity(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    states = (
        _state(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            status=HealthStatus.HEALTHY,
        ),
        _state(
            profile_id="impact-backup",
            service_id="impact",
            path_name="impact",
            status=HealthStatus.DEGRADED,
        ),
        _state(
            profile_id="impact-main",
            service_id="impact-backup",
            path_name="impact",
            status=HealthStatus.CRITICAL,
        ),
        _state(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact-backup",
            status=HealthStatus.UNKNOWN,
        ),
    )

    for state in states:
        repository.save(state=state)

    for state in states:
        assert repository.latest(
            profile_id=state.profile_id,
            service_id=state.service_id,
            path_name=state.path_name,
        ) == state


def test_latest_normalizes_identity_lookup(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)
    state = _state()

    repository.save(state=state)

    assert repository.latest(
        profile_id=" impact-main ",
        service_id=" impact ",
        path_name=" impact ",
    ) == state


def test_latest_rejects_blank_identity(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)

    try:
        repository.latest(
            profile_id=" ",
            service_id="impact",
            path_name="impact",
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "blank profile_id must be rejected"
        )
