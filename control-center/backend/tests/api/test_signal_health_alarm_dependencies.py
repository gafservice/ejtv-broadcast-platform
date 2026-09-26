"""Contract tests for Signal Health Alarm dependency composition."""

from unittest.mock import Mock

import app.api.dependencies as dependencies
from app.services.signal_health_transition_alarm_service import (
    SignalHealthTransitionAlarmService,
)


def test_signal_health_transition_alarm_service_uses_shared_alarm_service(
) -> None:
    dependencies.get_signal_health_transition_alarm_service.cache_clear()

    try:
        shared_alarm_service = dependencies.get_alarm_service()

        service = (
            dependencies.get_signal_health_transition_alarm_service()
        )

        assert isinstance(
            service,
            SignalHealthTransitionAlarmService,
        )
        assert service.alarm_service is shared_alarm_service
    finally:
        dependencies.get_signal_health_transition_alarm_service.cache_clear()


def test_session_observation_runtime_receives_signal_alarm_service(
    monkeypatch,
) -> None:
    mediamtx_adapter = Mock()
    session_adapter = Mock()
    streaming_service = Mock()
    operational_runtime = Mock()
    repository = Mock()
    signal_runtime = Mock()
    detector = Mock()
    event_service = Mock()
    alarm_service = Mock()

    profiles = (Mock(),)

    monkeypatch.setattr(
        dependencies,
        "get_mediamtx_adapter",
        lambda: mediamtx_adapter,
    )
    monkeypatch.setattr(
        dependencies,
        "get_mediamtx_session_adapter",
        lambda: session_adapter,
    )
    monkeypatch.setattr(
        dependencies,
        "get_streaming_service",
        lambda: streaming_service,
    )
    monkeypatch.setattr(
        dependencies,
        "get_session_operational_runtime",
        lambda: operational_runtime,
    )
    monkeypatch.setattr(
        dependencies,
        "get_media_health_current_state_repository",
        lambda: repository,
    )
    monkeypatch.setattr(
        dependencies,
        "get_signal_health_operational_runtime",
        lambda: signal_runtime,
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

    # The product does not provide this dependency yet.
    # raising=False lets this RED contract express the missing wiring.
    monkeypatch.setattr(
        dependencies,
        "get_signal_health_transition_alarm_service",
        lambda: alarm_service,
        raising=False,
    )

    loader = Mock()
    loader.load.return_value = profiles

    monkeypatch.setattr(
        dependencies,
        "NodeMediaProfileLoader",
        Mock(return_value=loader),
    )

    settings = Mock()
    settings.node_network_policy_path = "/tmp/node-policy.yaml"

    monkeypatch.setattr(
        dependencies,
        "get_settings",
        lambda: settings,
    )

    captured: dict[str, object] = {}

    class FakeSessionObservationRuntime:
        def __init__(
            self,
            *,
            mediamtx_adapter,
            session_adapter,
            streaming_service,
            operational_runtime,
            media_profiles,
            media_health_current_state_repository,
            signal_health_operational_runtime,
            signal_health_transition_detector,
            signal_health_transition_event_service,
            signal_health_transition_alarm_service,
        ) -> None:
            captured["mediamtx_adapter"] = mediamtx_adapter
            captured["session_adapter"] = session_adapter
            captured["streaming_service"] = streaming_service
            captured["operational_runtime"] = operational_runtime
            captured["media_profiles"] = media_profiles
            captured[
                "media_health_current_state_repository"
            ] = media_health_current_state_repository
            captured[
                "signal_health_operational_runtime"
            ] = signal_health_operational_runtime
            captured[
                "signal_health_transition_detector"
            ] = signal_health_transition_detector
            captured[
                "signal_health_transition_event_service"
            ] = signal_health_transition_event_service
            captured[
                "signal_health_transition_alarm_service"
            ] = signal_health_transition_alarm_service

    monkeypatch.setattr(
        dependencies,
        "SessionObservationRuntime",
        FakeSessionObservationRuntime,
    )

    dependencies.get_session_observation_runtime.cache_clear()

    try:
        dependencies.get_session_observation_runtime()
    finally:
        dependencies.get_session_observation_runtime.cache_clear()

    assert (
        captured["signal_health_transition_alarm_service"]
        is alarm_service
    )
