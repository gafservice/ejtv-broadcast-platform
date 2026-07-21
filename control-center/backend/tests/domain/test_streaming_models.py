"""Pruebas de los modelos del dominio multimedia."""

from datetime import datetime, timezone

from app.domain.streaming import (
    MediaMTXSnapshot,
    MediaPath,
    MediaPathStatus,
    MediaReader,
)


def test_media_path_exposes_derived_values() -> None:
    path = MediaPath(
        name="enlace",
        configuration_name="enlace",
        status=MediaPathStatus.ACTIVE,
        ready=True,
        available=True,
        online=True,
        readers=(
            MediaReader(
                reader_type="srtConn",
                reader_id="reader-1",
            ),
        ),
    )

    assert path.is_active is True
    assert path.reader_count == 1
    assert path.track_count == 0


def test_snapshot_calculates_global_totals() -> None:
    snapshot = MediaMTXSnapshot(
        captured_at=datetime.now(timezone.utc),
        reported_item_count=2,
        reported_page_count=1,
        paths=(
            MediaPath(
                name="enlace",
                configuration_name="enlace",
                status=MediaPathStatus.ACTIVE,
                ready=True,
                available=True,
                online=True,
                readers=(
                    MediaReader(reader_type="srtConn"),
                ),
            ),
            MediaPath(
                name="backup",
                configuration_name="backup",
                status=MediaPathStatus.NO_SOURCE,
                ready=False,
                available=False,
                online=False,
            ),
        ),
    )

    assert snapshot.path_count == 2
    assert snapshot.active_path_count == 1
    assert snapshot.total_reader_count == 1
    assert snapshot.get_path("enlace") is not None
    assert snapshot.get_path("missing") is None


def test_empty_snapshot_is_valid() -> None:
    snapshot = MediaMTXSnapshot.empty()

    assert snapshot.path_count == 0
    assert snapshot.active_path_count == 0
    assert snapshot.total_reader_count == 0
