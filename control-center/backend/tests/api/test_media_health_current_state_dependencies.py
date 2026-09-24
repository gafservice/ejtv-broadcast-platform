"""Composition-root contract for Media Health current state.

ENG-013C

The productive dependency graph must expose one shared SQLite-backed
Media Health current-state repository and inject that exact repository
into MediaOperationalCycleRuntime.

This contract does not start the application and does not use the
productive SQLite database.
"""

from __future__ import annotations

from functools import lru_cache

import app.api.dependencies as dependencies
from app.noc.current_state.sqlite_media_health_current_state_repository import (
    SQLiteMediaHealthCurrentStateRepository,
)
from app.noc.history.sqlite_database import SQLiteHistoryDatabase
from app.noc.runtime.media_operational_cycle_runtime import (
    MediaOperationalCycleRuntime,
)


def test_dependencies_exposes_media_health_current_state_repository_builder():
    assert hasattr(
        dependencies,
        "get_media_health_current_state_repository",
    )


def test_media_health_current_state_repository_builder_is_cached():
    builder = (
        dependencies.get_media_health_current_state_repository
    )

    assert hasattr(builder, "cache_info")
    assert hasattr(builder, "cache_clear")


def test_media_health_current_state_repository_uses_shared_history_database(
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
        dependencies.get_media_health_current_state_repository
    )
    builder.cache_clear()

    try:
        repository = builder()
    finally:
        builder.cache_clear()

    assert isinstance(
        repository,
        SQLiteMediaHealthCurrentStateRepository,
    )

    assert repository._database is database
    assert calls == ["database"]


def test_media_operational_cycle_runtime_receives_shared_current_state_repository(
    monkeypatch,
):
    repository = object()
    operational_runtime = object()

    monkeypatch.setattr(
        dependencies,
        "get_media_health_current_state_repository",
        lambda: repository,
    )

    monkeypatch.setattr(
        dependencies,
        "get_media_operational_runtime",
        lambda: operational_runtime,
    )

    captured: dict[str, object] = {}

    class FakeCycleRuntime:
        def __init__(
            self,
            *,
            operational_runtime,
            current_state_repository,
        ):
            captured["operational_runtime"] = (
                operational_runtime
            )
            captured["current_state_repository"] = (
                current_state_repository
            )

    monkeypatch.setattr(
        dependencies,
        "MediaOperationalCycleRuntime",
        FakeCycleRuntime,
    )

    dependencies.get_media_operational_cycle_runtime.cache_clear()

    try:
        runtime = (
            dependencies.get_media_operational_cycle_runtime()
        )
    finally:
        dependencies.get_media_operational_cycle_runtime.cache_clear()

    assert isinstance(runtime, FakeCycleRuntime)

    assert (
        captured["operational_runtime"]
        is operational_runtime
    )

    assert (
        captured["current_state_repository"]
        is repository
    )
