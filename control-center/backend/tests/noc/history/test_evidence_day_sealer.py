from datetime import date
from pathlib import Path

from app.noc.history.evidence_day_sealer import (
    EvidenceDaySealer,
)


def _day_directory(
    root: Path,
) -> Path:
    return (
        root
        / "2026"
        / "09"
        / "01"
    )


def test_seal_day_creates_manifest_and_primary_files(
    tmp_path,
) -> None:
    sealer = EvidenceDaySealer(tmp_path)

    result = sealer.seal_day(
        date(2026, 9, 1)
    )

    directory = _day_directory(
        tmp_path
    )

    assert result.created is True
    assert result.manifest_path == (
        directory
        / "manifest.sha256"
    )

    assert (
        directory
        / "events.jsonl"
    ).exists()

    assert (
        directory
        / "alarm_transitions.jsonl"
    ).exists()

    manifest = result.manifest_path.read_text(
        encoding="utf-8"
    )

    lines = manifest.splitlines()

    assert len(lines) == 2
    assert lines[0].endswith(
        "  alarm_transitions.jsonl"
    )
    assert lines[1].endswith(
        "  events.jsonl"
    )


def test_seal_day_is_idempotent(
    tmp_path,
) -> None:
    sealer = EvidenceDaySealer(tmp_path)

    first = sealer.seal_day(
        date(2026, 9, 1)
    )

    second = sealer.seal_day(
        date(2026, 9, 1)
    )

    assert first.created is True
    assert second.created is False

    assert (
        first.manifest_path.read_text(
            encoding="utf-8"
        )
        ==
        second.manifest_path.read_text(
            encoding="utf-8"
        )
    )


def test_verify_day_detects_tampering(
    tmp_path,
) -> None:
    sealer = EvidenceDaySealer(tmp_path)

    day = date(2026, 9, 1)

    sealer.seal_day(day)

    directory = _day_directory(
        tmp_path
    )

    assert sealer.verify_day(day) is True

    with (
        directory
        / "events.jsonl"
    ).open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            '{"tampered":true}\n'
        )

    assert sealer.verify_day(day) is False


def test_reseal_rejects_tampered_evidence(
    tmp_path,
) -> None:
    import pytest

    from app.noc.history.evidence_day_sealer import (
        EvidenceSealConflictError,
    )

    sealer = EvidenceDaySealer(tmp_path)

    day = date(2026, 9, 1)

    sealer.seal_day(day)

    directory = _day_directory(
        tmp_path
    )

    with (
        directory
        / "events.jsonl"
    ).open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            '{"tampered":true}\n'
        )

    with pytest.raises(
        EvidenceSealConflictError
    ):
        sealer.seal_day(day)


def test_verify_missing_evidence_file_does_not_recreate_it(
    tmp_path,
) -> None:
    day = date(
        2026,
        9,
        1,
    )

    sealer = EvidenceDaySealer(
        tmp_path
    )

    sealer.seal_day(day)

    directory = _day_directory(
        tmp_path
    )

    events_path = (
        directory
        / "events.jsonl"
    )

    events_path.unlink()

    assert not events_path.exists()

    assert sealer.verify_day(
        day
    ) is False

    assert not events_path.exists()


def test_reseal_rejects_missing_evidence_file(
    tmp_path,
) -> None:
    import pytest

    from app.noc.history.evidence_day_sealer import (
        EvidenceSealConflictError,
    )

    day = date(
        2026,
        9,
        1,
    )

    sealer = EvidenceDaySealer(
        tmp_path
    )

    sealer.seal_day(day)

    directory = _day_directory(
        tmp_path
    )

    events_path = (
        directory
        / "events.jsonl"
    )

    events_path.unlink()

    with pytest.raises(
        EvidenceSealConflictError
    ):
        sealer.seal_day(day)

    assert not events_path.exists()


def test_assert_day_can_be_finalized_allows_unsealed_day(
    tmp_path,
) -> None:
    sealer = EvidenceDaySealer(tmp_path)

    day = date(
        2026,
        9,
        1,
    )

    sealer.assert_day_can_be_finalized(
        day
    )


def test_assert_day_can_be_finalized_allows_valid_sealed_day(
    tmp_path,
) -> None:
    sealer = EvidenceDaySealer(tmp_path)

    day = date(
        2026,
        9,
        1,
    )

    sealer.seal_day(day)

    sealer.assert_day_can_be_finalized(
        day
    )


def test_assert_day_can_be_finalized_rejects_invalid_sealed_day(
    tmp_path,
) -> None:
    import pytest

    from app.noc.history.evidence_day_sealer import (
        EvidenceSealConflictError,
    )

    sealer = EvidenceDaySealer(tmp_path)

    day = date(
        2026,
        9,
        1,
    )

    sealer.seal_day(day)

    directory = _day_directory(
        tmp_path
    )

    with (
        directory
        / "events.jsonl"
    ).open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            '{"tampered":true}\n'
        )

    with pytest.raises(
        EvidenceSealConflictError
    ):
        sealer.assert_day_can_be_finalized(
            day
        )
