"""Composition-root contract for productive Signal Health.

ENG-013C

The productive dependency graph must:

- expose a shared Media Health freshness policy;
- expose a shared Media Health current-state resolver;
- expose a shared Signal Health operational runtime;
- configure freshness from Settings;
- reuse the shared Media Health current-state repository;
- load the same operational media profiles used by Media Health;
- inject the Signal Health handoff into SessionObservationRuntime.

This contract does not start the application, capture MediaMTX,
run ffprobe, or use the productive SQLite database.
"""

from __future__ import annotations

from unittest.mock import Mock

import app.api.dependencies as dependencies
from app.domain.streaming.expected_media_profile import (
    ExpectedMediaProfile,
)
from app.noc.current_state.media_health_current_state_resolver import (
    MediaHealthCurrentStateResolver,
)
from app.noc.current_state.media_health_freshness import (
    MediaHealthFreshnessPolicy,
)
from app.noc.runtime.session_observation_runtime import (
    SessionObservationRuntime,
)
from app.noc.runtime.signal_health_operational_runtime import (
    SignalHealthOperationalRuntime,
)


def _profile() -> ExpectedMediaProfile:
    return ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
    )


def test_dependencies_exposes_signal_health_builders() -> None:
    assert hasattr(
        dependencies,
        "get_media_health_freshness_policy",
    )
    assert hasattr(
        dependencies,
        "get_media_health_current_state_resolver",
    )
    assert hasattr(
        dependencies,
        "get_signal_health_operational_runtime",
    )


def test_signal_health_builders_are_cached() -> None:
    builders = (
        dependencies.get_media_health_freshness_policy,
        dependencies.get_media_health_current_state_resolver,
        dependencies.get_signal_health_operational_runtime,
    )

    for builder in builders:
        assert hasattr(builder, "cache_info")
        assert hasattr(builder, "cache_clear")


def test_media_health_freshness_policy_uses_settings(
    monkeypatch,
) -> None:
    settings = Mock()
    settings.media_health_freshness_max_age_seconds = 23.5

    monkeypatch.setattr(
        dependencies,
        "get_settings",
        lambda: settings,
    )

    captured: dict[str, object] = {}

    class FakeFreshnessPolicy:
        def __init__(
            self,
            *,
            max_age_seconds,
        ):
            captured["max_age_seconds"] = max_age_seconds

    monkeypatch.setattr(
        dependencies,
        "MediaHealthFreshnessPolicy",
        FakeFreshnessPolicy,
    )

    builder = dependencies.get_media_health_freshness_policy
    builder.cache_clear()

    try:
        policy = builder()
    finally:
        builder.cache_clear()

    assert isinstance(
        policy,
        FakeFreshnessPolicy,
    )
    assert captured["max_age_seconds"] == 23.5


def test_media_health_current_state_resolver_uses_shared_freshness_policy(
    monkeypatch,
) -> None:
    freshness_policy = object()

    monkeypatch.setattr(
        dependencies,
        "get_media_health_freshness_policy",
        lambda: freshness_policy,
    )

    captured: dict[str, object] = {}

    class FakeResolver:
        def __init__(
            self,
            *,
            freshness_policy,
        ):
            captured["freshness_policy"] = freshness_policy

    monkeypatch.setattr(
        dependencies,
        "MediaHealthCurrentStateResolver",
        FakeResolver,
    )

    builder = dependencies.get_media_health_current_state_resolver
    builder.cache_clear()

    try:
        resolver = builder()
    finally:
        builder.cache_clear()

    assert isinstance(
        resolver,
        FakeResolver,
    )
    assert (
        captured["freshness_policy"]
        is freshness_policy
    )


def test_signal_health_operational_runtime_uses_shared_components(
    monkeypatch,
) -> None:
    source_transport_evaluator = object()
    signal_health_evaluator = object()
    resolver = object()

    monkeypatch.setattr(
        dependencies,
        "get_source_transport_health_evaluator",
        lambda: source_transport_evaluator,
    )
    monkeypatch.setattr(
        dependencies,
        "get_signal_health_evaluator",
        lambda: signal_health_evaluator,
    )
    monkeypatch.setattr(
        dependencies,
        "get_media_health_current_state_resolver",
        lambda: resolver,
    )

    captured: dict[str, object] = {}

    class FakeSignalRuntime:
        def __init__(
            self,
            *,
            source_transport_health_evaluator,
            signal_health_evaluator,
            media_health_current_state_resolver,
        ):
            captured[
                "source_transport_health_evaluator"
            ] = source_transport_health_evaluator
            captured[
                "signal_health_evaluator"
            ] = signal_health_evaluator
            captured[
                "media_health_current_state_resolver"
            ] = media_health_current_state_resolver

    monkeypatch.setattr(
        dependencies,
        "SignalHealthOperationalRuntime",
        FakeSignalRuntime,
    )

    builder = dependencies.get_signal_health_operational_runtime
    builder.cache_clear()

    try:
        runtime = builder()
    finally:
        builder.cache_clear()

    assert isinstance(
        runtime,
        FakeSignalRuntime,
    )
    assert (
        captured["source_transport_health_evaluator"]
        is source_transport_evaluator
    )
    assert (
        captured["signal_health_evaluator"]
        is signal_health_evaluator
    )
    assert (
        captured["media_health_current_state_resolver"]
        is resolver
    )


def test_session_observation_runtime_receives_signal_health_handoff(
    monkeypatch,
) -> None:
    profile = _profile()
    profiles = (profile,)

    mediamtx_adapter = object()
    session_adapter = object()
    streaming_service = object()
    operational_runtime = object()
    current_state_repository = object()
    signal_runtime = object()

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
        lambda: current_state_repository,
    )
    monkeypatch.setattr(
        dependencies,
        "get_signal_health_operational_runtime",
        lambda: signal_runtime,
    )

    loader = Mock()
    loader.load.return_value = profiles

    loader_class = Mock(
        return_value=loader,
    )

    monkeypatch.setattr(
        dependencies,
        "NodeMediaProfileLoader",
        loader_class,
    )

    settings = Mock()
    settings.node_network_policy_path = (
        "/tmp/node-policy.yaml"
    )

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
        ):
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

    monkeypatch.setattr(
        dependencies,
        "SessionObservationRuntime",
        FakeSessionObservationRuntime,
    )

    dependencies.get_session_observation_runtime.cache_clear()

    try:
        runtime = (
            dependencies.get_session_observation_runtime()
        )
    finally:
        dependencies.get_session_observation_runtime.cache_clear()

    assert isinstance(
        runtime,
        FakeSessionObservationRuntime,
    )

    loader_class.assert_called_once_with()

    loader.load.assert_called_once_with(
        settings.node_network_policy_path,
    )

    assert captured["media_profiles"] == profiles

    assert (
        captured["media_health_current_state_repository"]
        is current_state_repository
    )

    assert (
        captured["signal_health_operational_runtime"]
        is signal_runtime
    )

    assert (
        captured["mediamtx_adapter"]
        is mediamtx_adapter
    )

    assert (
        captured["session_adapter"]
        is session_adapter
    )

    assert (
        captured["streaming_service"]
        is streaming_service
    )

    assert (
        captured["operational_runtime"]
        is operational_runtime
    )
