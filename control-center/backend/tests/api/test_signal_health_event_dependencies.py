"""Productive Signal Health event dependency contract.

ENG-013C — Block 231E

The composition root must expose shared Signal Health transition
components and inject them into SessionObservationRuntime.

This test does not capture MediaMTX, run the productive observation
cycle, start the application, or modify durable history.
"""

from __future__ import annotations

from unittest.mock import Mock

import app.api.dependencies as dependencies

from app.services.signal_health_transition_detector import (
    SignalHealthTransitionDetector,
)
from app.services.signal_health_transition_event_service import (
    SignalHealthTransitionEventService,
)


def _clear_signal_event_caches() -> None:
    """Clear only caches owned by this dependency contract."""

    for name in (
        "get_session_observation_runtime",
        "get_signal_health_transition_detector",
        "get_signal_health_transition_event_service",
        "get_event_service",
    ):
        dependency = getattr(dependencies, name, None)

        if dependency is not None and hasattr(
            dependency,
            "cache_clear",
        ):
            dependency.cache_clear()


def test_dependencies_exposes_signal_health_event_builders() -> None:
    assert hasattr(
        dependencies,
        "get_signal_health_transition_detector",
    )
    assert hasattr(
        dependencies,
        "get_signal_health_transition_event_service",
    )


def test_signal_health_transition_detector_is_shared() -> None:
    first = dependencies.get_signal_health_transition_detector()
    second = dependencies.get_signal_health_transition_detector()

    assert isinstance(
        first,
        SignalHealthTransitionDetector,
    )
    assert second is first


def test_signal_health_transition_event_service_is_shared_and_uses_event_service(
    monkeypatch,
) -> None:
    _clear_signal_event_caches()

    event_service = object()
    captured: dict[str, object] = {}

    class FakeSignalHealthTransitionEventService:
        def __init__(
            self,
            *,
            event_service,
        ) -> None:
            captured["event_service"] = event_service

    monkeypatch.setattr(
        dependencies,
        "get_event_service",
        lambda: event_service,
    )
    monkeypatch.setattr(
        dependencies,
        "SignalHealthTransitionEventService",
        FakeSignalHealthTransitionEventService,
    )

    try:
        service = (
            dependencies.get_signal_health_transition_event_service()
        )
    finally:
        _clear_signal_event_caches()

    assert isinstance(
        service,
        FakeSignalHealthTransitionEventService,
    )
    assert captured["event_service"] is event_service


def test_session_observation_runtime_receives_signal_event_dependencies(
    monkeypatch,
) -> None:
    _clear_signal_event_caches()

    detector = Mock(
        spec=SignalHealthTransitionDetector
    )
    event_service = Mock(
        spec=SignalHealthTransitionEventService
    )

    monkeypatch.setattr(
        dependencies,
        "get_signal_health_transition_detector",
        lambda: detector,
    )
    monkeypatch.setattr(
        dependencies,
        "get_signal_health_transition_event_service",
        lambda: event_service,
    )

    captured: dict[str, object] = {}

    class FakeSessionObservationRuntime:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(
        dependencies,
        "SessionObservationRuntime",
        FakeSessionObservationRuntime,
    )

    try:
        runtime = dependencies.get_session_observation_runtime()
    finally:
        _clear_signal_event_caches()

    assert isinstance(
        runtime,
        FakeSessionObservationRuntime,
    )

    assert (
        captured["signal_health_transition_detector"]
        is detector
    )
    assert (
        captured["signal_health_transition_event_service"]
        is event_service
    )
