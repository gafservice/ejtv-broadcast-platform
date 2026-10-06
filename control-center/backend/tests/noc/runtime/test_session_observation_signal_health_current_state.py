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
