from datetime import datetime, timezone

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.current_state.signal_health_current_state import (
    SignalHealthCurrentState,
    SignalHealthCurrentStateRepository,
)


OBSERVED_AT = datetime(
    2026,
    10,
    6,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


def _health(
    *,
    profile_id: str = "profile-enlace",
    service_id: str = "enlace",
    path_name: str | None = "enlace",
) -> SignalHealth:
    return SignalHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        media_status=HealthStatus.HEALTHY,
        transport_status=HealthStatus.HEALTHY,
        status=HealthStatus.HEALTHY,
    )


def test_current_state_preserves_canonical_signal_health() -> None:
    health = _health()

    state = SignalHealthCurrentState(
        profile_id="profile-enlace",
        service_id="enlace",
        path_name="enlace",
        observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
        health=health,
    )

    assert state.profile_id == "profile-enlace"
    assert state.service_id == "enlace"
    assert state.path_name == "enlace"
    assert state.observed_at == OBSERVED_AT
    assert state.health is health


def test_current_state_is_immutable() -> None:
    state = SignalHealthCurrentState(
        profile_id="profile-enlace",
        service_id="enlace",
        path_name="enlace",
        observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
        health=_health(),
    )

    with pytest.raises(AttributeError):
        state.service_id = "changed"  # type: ignore[misc]


def test_current_state_normalizes_identity() -> None:
    state = SignalHealthCurrentState(
        profile_id=" profile-enlace ",
        service_id=" enlace ",
        path_name=" enlace ",
        observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
        health=_health(),
    )

    assert state.profile_id == "profile-enlace"
    assert state.service_id == "enlace"
    assert state.path_name == "enlace"


@pytest.mark.parametrize(
    "field_name",
    (
        "profile_id",
        "service_id",
        "path_name",
    ),
)
def test_current_state_rejects_blank_identity(
    field_name: str,
) -> None:
    values = {
        "profile_id": "profile-enlace",
        "service_id": "enlace",
        "path_name": "enlace",
    }
    values[field_name] = "   "

    with pytest.raises(ValueError):
        SignalHealthCurrentState(
            **values,
            observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
            health=_health(),
        )


def test_current_state_requires_timezone_aware_observed_at() -> None:
    with pytest.raises(ValueError):
        SignalHealthCurrentState(
            profile_id="profile-enlace",
            service_id="enlace",
            path_name="enlace",
            observed_at=datetime(2026, 10, 6, 12, 0, 0),
        health_since=OBSERVED_AT,
            health=_health(),
        )


def test_current_state_requires_signal_health() -> None:
    with pytest.raises(TypeError):
        SignalHealthCurrentState(
            profile_id="profile-enlace",
            service_id="enlace",
            path_name="enlace",
            observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
            health="not-health",  # type: ignore[arg-type]
        )


def test_current_state_identity_must_match_health() -> None:
    with pytest.raises(ValueError):
        SignalHealthCurrentState(
            profile_id="profile-enlace",
            service_id="other-service",
            path_name="enlace",
            observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
            health=_health(),
        )


def test_repository_port_exposes_save_and_latest() -> None:
    assert hasattr(SignalHealthCurrentStateRepository, "save")
    assert hasattr(SignalHealthCurrentStateRepository, "latest")


def test_repository_port_is_runtime_checkable_protocol() -> None:
    class Repository:
        def save(
            self,
            *,
            state: SignalHealthCurrentState,
        ) -> None:
            pass

        def latest(
            self,
            *,
            profile_id: str,
            service_id: str,
            path_name: str,
        ) -> SignalHealthCurrentState | None:
            return None

    assert isinstance(
        Repository(),
        SignalHealthCurrentStateRepository,
    )


def test_repository_save_requires_keyword_state() -> None:
    import inspect

    parameter = inspect.signature(
        SignalHealthCurrentStateRepository.save
    ).parameters["state"]

    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize(
    "field_name",
    (
        "profile_id",
        "service_id",
        "path_name",
    ),
)
def test_current_state_rejects_non_string_identity(
    field_name: str,
) -> None:
    values = {
        "profile_id": "profile-enlace",
        "service_id": "enlace",
        "path_name": "enlace",
    }
    values[field_name] = 123  # type: ignore[assignment]

    with pytest.raises(
        TypeError,
        match=rf"{field_name} must be a string",
    ):
        SignalHealthCurrentState(
            **values,
            observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
            health=_health(),
        )

# ENG-013C 235E.23 — Health Since temporal contract.

def test_signal_health_current_state_requires_health_since() -> None:
    health = _health()

    state = SignalHealthCurrentState(
        profile_id=health.profile_id,
        service_id=health.service_id,
        path_name=health.path_name,
        observed_at=OBSERVED_AT,
        health_since=OBSERVED_AT,
        health=health,
    )

    assert state.health_since is OBSERVED_AT


def test_signal_health_current_state_rejects_naive_health_since() -> None:
    health = _health()
    naive_since = OBSERVED_AT.replace(tzinfo=None)

    with pytest.raises((TypeError, ValueError)):
        SignalHealthCurrentState(
            profile_id=health.profile_id,
            service_id=health.service_id,
            path_name=health.path_name,
            observed_at=OBSERVED_AT,
            health_since=naive_since,
            health=health,
        )

def test_signal_health_current_state_rejects_future_health_since() -> None:
    from datetime import timedelta

    health = _health()
    future_since = OBSERVED_AT + timedelta(microseconds=1)

    with pytest.raises((TypeError, ValueError)):
        SignalHealthCurrentState(
            profile_id=health.profile_id,
            service_id=health.service_id,
            path_name=health.path_name,
            observed_at=OBSERVED_AT,
            health_since=future_since,
            health=health,
        )
