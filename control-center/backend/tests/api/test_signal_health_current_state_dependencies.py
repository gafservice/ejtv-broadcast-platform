"""Composition-root contract for Signal Health current state.

ENG-013C

The productive dependency graph must expose one shared SQLite-backed
Signal Health current-state repository and inject that exact repository
into SessionObservationRuntime.

This contract does not start the application and does not use the
productive SQLite database.
"""

from __future__ import annotations

import app.api.dependencies as dependencies
from app.noc.current_state.sqlite_signal_health_current_state_repository import (
    SQLiteSignalHealthCurrentStateRepository,
)
from app.noc.history.sqlite_database import SQLiteHistoryDatabase


def test_dependencies_exposes_signal_health_current_state_repository_builder():
    assert hasattr(
        dependencies,
        "get_signal_health_current_state_repository",
    )


def test_signal_health_current_state_repository_builder_is_cached():
    builder = (
        dependencies.get_signal_health_current_state_repository
    )

    assert hasattr(builder, "cache_info")
    assert hasattr(builder, "cache_clear")


def test_signal_health_current_state_repository_uses_shared_history_database(
    monkeypatch,
    tmp_path,
):
    database = SQLiteHistoryDatabase(
        tmp_path / "noc-history.db"
    )

    calls: list[str] = []

    def fake_database():
        calls.append("database")
        return database

    monkeypatch.setattr(
        dependencies,
        "get_noc_history_database",
        fake_database,
    )

    builder = (
        dependencies.get_signal_health_current_state_repository
    )
    builder.cache_clear()

    try:
        repository = builder()
    finally:
        builder.cache_clear()

    assert isinstance(
        repository,
        SQLiteSignalHealthCurrentStateRepository,
    )
    assert repository._database is database
    assert calls == ["database"]


def test_session_observation_runtime_receives_shared_signal_current_state_repository(
    monkeypatch,
):
    repository = object()

    monkeypatch.setattr(
        dependencies,
        "get_signal_health_current_state_repository",
        lambda: repository,
        raising=False,
    )

    captured: dict[str, object] = {}

    original_runtime = dependencies.SessionObservationRuntime

    class CapturingSessionObservationRuntime:
        def __init__(
            self,
            **kwargs,
        ):
            captured.update(kwargs)

    monkeypatch.setattr(
        dependencies,
        "SessionObservationRuntime",
        CapturingSessionObservationRuntime,
    )

    dependencies.get_session_observation_runtime.cache_clear()

    try:
        runtime = (
            dependencies.get_session_observation_runtime()
        )
    finally:
        dependencies.get_session_observation_runtime.cache_clear()
        monkeypatch.setattr(
            dependencies,
            "SessionObservationRuntime",
            original_runtime,
        )

    assert isinstance(
        runtime,
        CapturingSessionObservationRuntime,
    )

    assert (
        captured[
            "signal_health_current_state_repository"
        ]
        is repository
    )
