from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.current_state.signal_health_current_state import (
    SignalHealthCurrentState,
)


NOW = datetime(
    2026,
    10,
    6,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def _signal_health(
    *,
    path_name: str | None = "impact",
) -> SignalHealth:
    return SignalHealth(
        profile_id="impact-main",
        service_id="impact",
        path_name=path_name,
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.HEALTHY,
    )


def test_path_backed_signal_health_current_state_contract() -> None:
    health = _signal_health()

    state = SignalHealthCurrentState(
        profile_id=health.profile_id,
        service_id=health.service_id,
        path_name=health.path_name,
        observed_at=NOW,
        health_since=NOW,
        health=health,
    )

    assert state.profile_id == "impact-main"
    assert state.service_id == "impact"
    assert state.path_name == "impact"
    assert state.observed_at is NOW
    assert state.health is health


def test_pathless_signal_health_is_not_valid_for_path_backed_current_state() -> None:
    health = _signal_health(
        path_name=None,
    )

    with pytest.raises(
        (TypeError, ValueError),
    ):
        SignalHealthCurrentState(
            profile_id=health.profile_id,
            service_id=health.service_id,
            path_name=health.path_name,
            observed_at=NOW,
            health=health,
        )


def test_session_runtime_accepts_signal_health_current_state_repository() -> None:
    from app.noc.runtime.session_observation_runtime import (
        SessionObservationRuntime,
    )

    parameters = (
        SessionObservationRuntime.__init__.__annotations__
    )

    assert (
        "signal_health_current_state_repository"
        in parameters
    )


def test_writer_contract_uses_canonical_signal_health_identity_and_time() -> None:
    repository = Mock()
    health = _signal_health()

    state = SignalHealthCurrentState(
        profile_id=health.profile_id,
        service_id=health.service_id,
        path_name=health.path_name,
        observed_at=NOW,
        health_since=NOW,
        health=health,
    )

    repository.save(
        state=state,
    )

    repository.save.assert_called_once_with(
        state=state,
    )

    saved = repository.save.call_args.kwargs["state"]

    assert saved.profile_id == health.profile_id
    assert saved.service_id == health.service_id
    assert saved.path_name == health.path_name
    assert saved.observed_at == NOW
    assert saved.health is health

def test_writer_persists_path_backed_canonical_signal_health() -> None:
    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentStateRepository,
    )
    from app.noc.current_state.signal_health_current_state import (
        SignalHealthCurrentStateRepository,
    )
    from app.noc.runtime.signal_health_operational_runtime import (
        SignalHealthOperationalRuntime,
    )
    from tests.noc.runtime.test_session_observation_signal_health_handoff import (
        INSTANCE_ID,
        NODE_ID,
        NOW,
        _build_runtime,
        _signal_health as canonical_signal_health,
    )

    media_repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    media_repository.latest.return_value = None

    signal_current_state_repository = Mock(
        spec=SignalHealthCurrentStateRepository
    )
    signal_current_state_repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )

    health = canonical_signal_health()

    signal_runtime.process_current_state.return_value = health

    runtime, *_ = _build_runtime(
        repository=media_repository,
        signal_runtime=signal_runtime,
    )

    runtime._signal_health_current_state_repository = (
        signal_current_state_repository
    )

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    signal_current_state_repository.save.assert_called_once()

    saved = (
        signal_current_state_repository
        .save
        .call_args
        .kwargs["state"]
    )

    assert isinstance(
        saved,
        SignalHealthCurrentState,
    )
    assert saved.profile_id == health.profile_id
    assert saved.service_id == health.service_id
    assert saved.path_name == health.path_name
    assert saved.observed_at == NOW
    assert saved.health is health


def test_writer_contract_preserves_pathless_domain_without_inventing_path() -> None:
    health = _signal_health(
        path_name=None,
    )

    assert health.path_name is None

    with pytest.raises(
        (TypeError, ValueError),
    ):
        SignalHealthCurrentState(
            profile_id=health.profile_id,
            service_id=health.service_id,
            path_name=health.path_name,
            observed_at=NOW,
            health=health,
        )


# ENG-013C 235E.23J.3B — Health Since temporal writer contract.


def _saved_signal_current_state(
    repository,
):
    repository.save.assert_called_once()
    return repository.save.call_args.kwargs["state"]


def test_writer_first_observation_starts_health_since_at_observed_at() -> None:
    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentStateRepository,
    )
    from app.noc.current_state.signal_health_current_state import (
        SignalHealthCurrentStateRepository,
    )
    from app.noc.runtime.signal_health_operational_runtime import (
        SignalHealthOperationalRuntime,
    )
    from tests.noc.runtime.test_session_observation_signal_health_handoff import (
        INSTANCE_ID,
        NODE_ID,
        NOW,
        _build_runtime,
        _signal_health as canonical_signal_health,
    )

    media_repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    media_repository.latest.return_value = None

    signal_repository = Mock(
        spec=SignalHealthCurrentStateRepository
    )
    signal_repository.latest.return_value = None

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    health = canonical_signal_health()
    signal_runtime.process_current_state.return_value = health

    runtime, *_ = _build_runtime(
        repository=media_repository,
        signal_runtime=signal_runtime,
    )
    runtime._signal_health_current_state_repository = signal_repository

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    saved = _saved_signal_current_state(signal_repository)

    assert saved.observed_at == NOW
    assert saved.health_since == NOW


def test_writer_same_status_preserves_previous_health_since() -> None:
    from datetime import timedelta

    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentStateRepository,
    )
    from app.noc.current_state.signal_health_current_state import (
        SignalHealthCurrentState,
        SignalHealthCurrentStateRepository,
    )
    from app.noc.runtime.signal_health_operational_runtime import (
        SignalHealthOperationalRuntime,
    )
    from tests.noc.runtime.test_session_observation_signal_health_handoff import (
        INSTANCE_ID,
        NODE_ID,
        NOW,
        _build_runtime,
        _signal_health as canonical_signal_health,
    )

    media_repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    media_repository.latest.return_value = None

    signal_repository = Mock(
        spec=SignalHealthCurrentStateRepository
    )

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    health = canonical_signal_health()
    signal_runtime.process_current_state.return_value = health

    previous_since = NOW - timedelta(minutes=12)

    signal_repository.latest.return_value = SignalHealthCurrentState(
        profile_id=health.profile_id,
        service_id=health.service_id,
        path_name=health.path_name,
        observed_at=NOW - timedelta(seconds=5),
        health_since=previous_since,
        health=health,
    )

    runtime, *_ = _build_runtime(
        repository=media_repository,
        signal_runtime=signal_runtime,
    )
    runtime._signal_health_current_state_repository = signal_repository

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    saved = _saved_signal_current_state(signal_repository)

    assert saved.observed_at == NOW
    assert saved.health.status is health.status
    assert saved.health_since == previous_since


def test_writer_status_change_resets_health_since_to_observed_at() -> None:
    from datetime import timedelta

    from app.domain.streaming.health import HealthStatus
    from app.domain.streaming.signal_health import SignalHealth
    from app.noc.current_state.media_health_current_state import (
        MediaHealthCurrentStateRepository,
    )
    from app.noc.current_state.signal_health_current_state import (
        SignalHealthCurrentState,
        SignalHealthCurrentStateRepository,
    )
    from app.noc.runtime.signal_health_operational_runtime import (
        SignalHealthOperationalRuntime,
    )
    from tests.noc.runtime.test_session_observation_signal_health_handoff import (
        INSTANCE_ID,
        NODE_ID,
        NOW,
        _build_runtime,
        _signal_health as canonical_signal_health,
    )

    media_repository = Mock(
        spec=MediaHealthCurrentStateRepository
    )
    media_repository.latest.return_value = None

    signal_repository = Mock(
        spec=SignalHealthCurrentStateRepository
    )

    signal_runtime = Mock(
        spec=SignalHealthOperationalRuntime
    )
    current = canonical_signal_health()
    signal_runtime.process_current_state.return_value = current

    previous = SignalHealth(
        profile_id=current.profile_id,
        service_id=current.service_id,
        path_name=current.path_name,
        media_status=HealthStatus.DEGRADED,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.DEGRADED,
    )

    signal_repository.latest.return_value = SignalHealthCurrentState(
        profile_id=previous.profile_id,
        service_id=previous.service_id,
        path_name=previous.path_name,
        observed_at=NOW - timedelta(seconds=5),
        health_since=NOW - timedelta(minutes=20),
        health=previous,
    )

    runtime, *_ = _build_runtime(
        repository=media_repository,
        signal_runtime=signal_runtime,
    )
    runtime._signal_health_current_state_repository = signal_repository

    runtime.run_once(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
    )

    saved = _saved_signal_current_state(signal_repository)

    assert saved.observed_at == NOW
    assert saved.health.status is current.status
    assert saved.health_since == NOW
