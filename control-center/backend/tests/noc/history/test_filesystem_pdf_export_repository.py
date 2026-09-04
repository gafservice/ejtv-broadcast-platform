"""Tests for filesystem publication of derived PDF history."""

from __future__ import annotations

import pytest

from app.noc.history.filesystem_pdf_export_repository import (
    FilesystemPdfExportRepository,
)


PDF_DOCUMENT = (
    b"%PDF-1.4\n"
    b"derived-history-report\n"
    b"%%EOF\n"
)


def test_publish_creates_exact_pdf_export(
    tmp_path,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    destination = (
        tmp_path
        / "export-001"
    )

    result = repository.publish(
        destination=destination,
        pdf_document=PDF_DOCUMENT,
    )

    assert result.path == destination
    assert result.report_file == (
        destination
        / "history-report.pdf"
    )

    assert [
        path.name
        for path in destination.iterdir()
    ] == [
        "history-report.pdf",
    ]

    assert (
        destination
        / "history-report.pdf"
    ).read_bytes() == PDF_DOCUMENT


def test_existing_export_is_never_overwritten(
    tmp_path,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    destination = (
        tmp_path
        / "existing"
    )

    destination.mkdir()

    marker = (
        destination
        / "existing.txt"
    )
    marker.write_text(
        "preserve",
        encoding="utf-8",
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.publish(
            destination=destination,
            pdf_document=PDF_DOCUMENT,
        )

    assert marker.read_text(
        encoding="utf-8"
    ) == "preserve"


def test_invalid_destination_type_publishes_nothing(
    tmp_path,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    with pytest.raises(
        TypeError,
        match="destination must be a Path",
    ):
        repository.publish(
            destination=str(
                tmp_path
                / "invalid"
            ),
            pdf_document=PDF_DOCUMENT,
        )


def test_invalid_pdf_document_type_is_rejected(
    tmp_path,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    destination = (
        tmp_path
        / "invalid-content"
    )

    with pytest.raises(
        TypeError,
        match="pdf_document must be bytes",
    ):
        repository.publish(
            destination=destination,
            pdf_document="%PDF",
        )

    assert not destination.exists()


def test_publication_failure_removes_temporary_directory(
    tmp_path,
    monkeypatch,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    destination = (
        tmp_path
        / "failed-export"
    )

    def fail_publish(
        *,
        temporary,
        destination,
    ):
        raise OSError(
            "simulated publication failure"
        )

    monkeypatch.setattr(
        repository,
        "_publish_without_overwrite",
        fail_publish,
    )

    with pytest.raises(
        OSError,
        match="simulated publication failure",
    ):
        repository.publish(
            destination=destination,
            pdf_document=PDF_DOCUMENT,
        )

    assert not destination.exists()

    assert not any(
        path.name.startswith(
            ".failed-export."
        )
        for path in tmp_path.iterdir()
    )


def test_parent_directory_is_created(
    tmp_path,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    destination = (
        tmp_path
        / "nested"
        / "exports"
        / "export-001"
    )

    repository.publish(
        destination=destination,
        pdf_document=PDF_DOCUMENT,
    )

    assert destination.is_dir()

    assert (
        destination
        / "history-report.pdf"
    ).read_bytes() == PDF_DOCUMENT


def test_concurrent_winner_is_never_replaced(
    tmp_path,
    monkeypatch,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    destination = (
        tmp_path
        / "race-export"
    )

    original_publish = (
        repository._publish_without_overwrite
    )

    def publish_after_concurrent_winner(
        *,
        temporary,
        destination,
    ):
        destination.mkdir()

        marker = (
            destination
            / "winner.txt"
        )
        marker.write_text(
            "concurrent-winner",
            encoding="utf-8",
        )

        return original_publish(
            temporary=temporary,
            destination=destination,
        )

    monkeypatch.setattr(
        repository,
        "_publish_without_overwrite",
        publish_after_concurrent_winner,
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        repository.publish(
            destination=destination,
            pdf_document=PDF_DOCUMENT,
        )

    assert (
        destination
        / "winner.txt"
    ).read_text(
        encoding="utf-8"
    ) == "concurrent-winner"

    assert not (
        destination
        / "history-report.pdf"
    ).exists()

    assert not any(
        path.name.startswith(
            ".race-export."
        )
        for path in tmp_path.iterdir()
    )


def test_parent_fsync_failure_keeps_published_export(
    tmp_path,
    monkeypatch,
) -> None:
    repository = (
        FilesystemPdfExportRepository()
    )

    destination = (
        tmp_path
        / "fsync-failure"
    )

    original_fsync = (
        repository._fsync_directory
    )

    def fail_parent_fsync(
        directory,
    ):
        if directory == tmp_path:
            raise OSError(
                "simulated parent fsync failure"
            )

        return original_fsync(
            directory
        )

    monkeypatch.setattr(
        repository,
        "_fsync_directory",
        fail_parent_fsync,
    )

    with pytest.raises(
        OSError,
        match="simulated parent fsync failure",
    ):
        repository.publish(
            destination=destination,
            pdf_document=PDF_DOCUMENT,
        )

    assert destination.is_dir()

    assert (
        destination
        / "history-report.pdf"
    ).read_bytes() == PDF_DOCUMENT

    assert not any(
        path.name.startswith(
            ".fsync-failure."
        )
        for path in tmp_path.iterdir()
    )
