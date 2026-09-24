"""Contract tests for Media Health shared current state.

ENG-013C — Media Health Current State

The current-state projection is the handoff boundary between the
independent Media Health observation cycle and consumers that need the
latest stabilized Media Health conclusion.

It is not durable operational history and it does not perform capture,
media observation, transport evaluation, Signal Health evaluation, or
temporal stabilization.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.media_health import MediaHealth
from app.noc.current_state.media_health_current_state import (
    MediaHealthCurrentState,
    MediaHealthCurrentStateRepository,
)


OBSERVED_AT = datetime(
    2026,
    9,
    23,
    22,
    0,
    0,
    tzinfo=timezone.utc,
)


def _media_health(
    *,
    profile_id: str = "impact-main",
    service_id: str = "impact",
    path_name: str = "impact",
    status: HealthStatus = HealthStatus.HEALTHY,
) -> MediaHealth:
    return MediaHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        status=status,
    )


def test_current_state_preserves_identity_health_and_observed_at() -> None:
    health = _media_health()

    state = MediaHealthCurrentState(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        observed_at=OBSERVED_AT,
        health=health,
    )

    assert state.profile_id == "impact-main"
    assert state.service_id == "impact"
    assert state.path_name == "impact"
    assert state.observed_at == OBSERVED_AT
    assert state.health is health


def test_current_state_is_immutable() -> None:
    state = MediaHealthCurrentState(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        observed_at=OBSERVED_AT,
        health=_media_health(),
    )

    with pytest.raises(FrozenInstanceError):
        state.service_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("profile_id", ""),
        ("profile_id", "   "),
        ("service_id", ""),
        ("service_id", "   "),
        ("path_name", ""),
        ("path_name", "   "),
    ),
)
def test_current_state_rejects_blank_identity(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "profile_id": "impact-main",
        "service_id": "impact",
        "path_name": "impact",
        "observed_at": OBSERVED_AT,
        "health": _media_health(),
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError):
        MediaHealthCurrentState(**kwargs)


def test_current_state_normalizes_identity() -> None:
    state = MediaHealthCurrentState(
        profile_id="  impact-main  ",
        service_id="  impact  ",
        path_name="  impact  ",
        observed_at=OBSERVED_AT,
        health=_media_health(),
    )

    assert state.profile_id == "impact-main"
    assert state.service_id == "impact"
    assert state.path_name == "impact"


def test_current_state_requires_timezone_aware_observed_at() -> None:
    with pytest.raises(
        ValueError,
        match="observed_at must be timezone-aware",
    ):
        MediaHealthCurrentState(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            observed_at=datetime(2026, 9, 23, 22, 0, 0),
            health=_media_health(),
        )


def test_current_state_requires_media_health() -> None:
    with pytest.raises(
        TypeError,
        match="health must be a MediaHealth",
    ):
        MediaHealthCurrentState(
            profile_id="impact-main",
            service_id="impact",
            path_name="impact",
            observed_at=OBSERVED_AT,
            health=object(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("profile_id", "other-profile"),
        ("service_id", "other-service"),
        ("path_name", "other-path"),
    ),
)
def test_current_state_requires_identity_to_match_health(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "profile_id": "impact-main",
        "service_id": "impact",
        "path_name": "impact",
        "observed_at": OBSERVED_AT,
        "health": _media_health(),
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match="identity"):
        MediaHealthCurrentState(**kwargs)


def test_repository_contract_exposes_save_and_latest() -> None:
    assert hasattr(MediaHealthCurrentStateRepository, "save")
    assert hasattr(MediaHealthCurrentStateRepository, "latest")


def test_repository_contract_is_runtime_checkable() -> None:
    class Repository:
        def save(self, *, state: MediaHealthCurrentState) -> None:
            pass

        def latest(
            self,
            *,
            profile_id: str,
            service_id: str,
            path_name: str,
        ) -> MediaHealthCurrentState | None:
            return None

    assert isinstance(
        Repository(),
        MediaHealthCurrentStateRepository,
    )
