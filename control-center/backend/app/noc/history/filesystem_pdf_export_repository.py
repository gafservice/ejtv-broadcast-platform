"""Filesystem adapter for derived NOC history PDF exports.

ENG-013B — Operational History.

One export is published as one immutable directory containing exactly:

- history-report.pdf

PDF is a derived representation. This adapter does not query SQLite,
decide history ranges, render reports, seal evidence, perform retention,
or own backup policy.
"""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import uuid
from pathlib import Path

from app.noc.history.pdf_export_repository import (
    PdfExportRepository,
    PdfExportResult,
)


class FilesystemPdfExportRepository(PdfExportRepository):
    """Atomically publish one derived PDF history report."""

    REPORT_FILENAME = "history-report.pdf"

    def publish(
        self,
        *,
        destination: Path,
        pdf_document: bytes,
    ) -> PdfExportResult:
        self._validate_destination(
            destination
        )
        self._validate_pdf_document(
            pdf_document
        )

        if destination.exists():
            raise FileExistsError(
                "PDF export destination already exists: "
                f"{destination}"
            )

        parent = destination.parent
        parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = parent / (
            f".{destination.name}."
            f"{uuid.uuid4().hex}.tmp"
        )

        published = False

        try:
            temporary.mkdir()

            report_file = (
                temporary
                / self.REPORT_FILENAME
            )

            self._write_binary_file(
                report_file,
                pdf_document,
            )

            self._fsync_directory(
                temporary
            )

            self._publish_without_overwrite(
                temporary=temporary,
                destination=destination,
            )

            published = True

            self._fsync_directory(
                parent
            )

            return PdfExportResult(
                path=destination,
                report_file=(
                    destination
                    / self.REPORT_FILENAME
                ),
            )
        finally:
            if (
                not published
                and temporary.exists()
            ):
                shutil.rmtree(
                    temporary
                )

    @staticmethod
    def _write_binary_file(
        path: Path,
        content: bytes,
    ) -> None:
        with path.open(
            "xb"
        ) as handle:
            handle.write(
                content
            )
            handle.flush()
            os.fsync(
                handle.fileno()
            )

    @staticmethod
    def _publish_without_overwrite(
        *,
        temporary: Path,
        destination: Path,
    ) -> None:
        """Atomically publish a directory without replacement."""

        libc = ctypes.CDLL(
            None,
            use_errno=True,
        )

        renameat2 = getattr(
            libc,
            "renameat2",
            None,
        )

        if renameat2 is None:
            raise RuntimeError(
                "atomic PDF publication requires "
                "renameat2(RENAME_NOREPLACE)"
            )

        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int

        at_fdcwd = -100
        rename_noreplace = 1

        result = renameat2(
            at_fdcwd,
            os.fsencode(temporary),
            at_fdcwd,
            os.fsencode(destination),
            rename_noreplace,
        )

        if result == 0:
            return

        error_number = ctypes.get_errno()

        if error_number in (
            errno.EEXIST,
            errno.ENOTEMPTY,
        ):
            raise FileExistsError(
                "PDF export destination already exists: "
                f"{destination}"
            )

        raise OSError(
            error_number,
            os.strerror(error_number),
            destination,
        )

    @staticmethod
    def _fsync_directory(
        directory: Path,
    ) -> None:
        descriptor = os.open(
            directory,
            os.O_RDONLY,
        )

        try:
            os.fsync(
                descriptor
            )
        finally:
            os.close(
                descriptor
            )

    @staticmethod
    def _validate_destination(
        destination: Path,
    ) -> None:
        if not isinstance(
            destination,
            Path,
        ):
            raise TypeError(
                "destination must be a Path"
            )

    @staticmethod
    def _validate_pdf_document(
        value: bytes,
    ) -> None:
        if not isinstance(
            value,
            bytes,
        ):
            raise TypeError(
                "pdf_document must be bytes"
            )
