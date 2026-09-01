from datetime import date

from app.noc.history.daily_evidence_lock import (
    DailyEvidenceLock,
)


def test_day_directory_uses_utc_calendar_layout(
    tmp_path,
) -> None:
    lock = DailyEvidenceLock(tmp_path)

    directory = lock.day_directory(
        date(2026, 9, 1)
    )

    assert directory == (
        tmp_path
        / "2026"
        / "09"
        / "01"
    )


def test_exclusive_creates_persistent_lock_file(
    tmp_path,
) -> None:
    lock = DailyEvidenceLock(tmp_path)

    day = date(2026, 9, 1)

    with lock.exclusive(day) as directory:
        assert directory == (
            tmp_path
            / "2026"
            / "09"
            / "01"
        )

        assert (
            directory
            / ".evidence.lock"
        ).exists()

    assert (
        tmp_path
        / "2026"
        / "09"
        / "01"
        / ".evidence.lock"
    ).exists()
