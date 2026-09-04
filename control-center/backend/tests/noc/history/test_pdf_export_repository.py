"""Contract tests for derived PDF history export publication."""

from pathlib import Path

import pytest

from app.noc.history.pdf_export_repository import (
    PdfExportRepository,
    PdfExportResult,
)


class FakePdfExportRepository:
    """Minimal structural implementation of the PDF export port."""

    def publish(
        self,
        *,
        destination: Path,
        pdf_document: bytes,
    ) -> PdfExportResult:
        return PdfExportResult(
            path=destination,
            report_file=destination / "history-report.pdf",
        )


def test_pdf_export_result_accepts_paths() -> None:
    destination = Path("/tmp/export")

    result = PdfExportResult(
        path=destination,
        report_file=destination / "history-report.pdf",
    )

    assert result.path == destination
    assert result.report_file == destination / "history-report.pdf"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", "/tmp/export"),
        ("report_file", "/tmp/export/history-report.pdf"),
    ],
)
def test_pdf_export_result_requires_paths(
    field: str,
    value: str,
) -> None:
    values = {
        "path": Path("/tmp/export"),
        "report_file": Path("/tmp/export/history-report.pdf"),
    }
    values[field] = value

    with pytest.raises(
        TypeError,
        match=f"{field} must be a Path",
    ):
        PdfExportResult(**values)


def test_pdf_export_repository_is_runtime_checkable() -> None:
    repository = FakePdfExportRepository()

    assert isinstance(
        repository,
        PdfExportRepository,
    )


def test_pdf_export_repository_publish_contract() -> None:
    repository = FakePdfExportRepository()
    destination = Path("/tmp/export")

    result = repository.publish(
        destination=destination,
        pdf_document=b"%PDF-test",
    )

    assert result == PdfExportResult(
        path=destination,
        report_file=destination / "history-report.pdf",
    )
