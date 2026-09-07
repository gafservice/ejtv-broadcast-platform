import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_stream_health_temporal_policy_is_disabled_by_default(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "STREAM_HEALTH_SRT_DEGRADATION_SECONDS",
        raising=False,
    )
    monkeypatch.delenv(
        "STREAM_HEALTH_SRT_RECOVERY_SECONDS",
        raising=False,
    )

    settings = Settings(_env_file=None)

    assert (
        settings.stream_health_srt_degradation_seconds
        is None
    )
    assert (
        settings.stream_health_srt_recovery_seconds
        is None
    )


def test_stream_health_temporal_policy_accepts_complete_pair(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "STREAM_HEALTH_SRT_DEGRADATION_SECONDS",
        "7.5",
    )
    monkeypatch.setenv(
        "STREAM_HEALTH_SRT_RECOVERY_SECONDS",
        "12.0",
    )

    settings = Settings(_env_file=None)

    assert (
        settings.stream_health_srt_degradation_seconds
        == 7.5
    )
    assert (
        settings.stream_health_srt_recovery_seconds
        == 12.0
    )


@pytest.mark.parametrize(
    (
        "degradation",
        "recovery",
    ),
    (
        ("5.0", None),
        (None, "5.0"),
    ),
)
def test_stream_health_temporal_policy_rejects_partial_pair(
    monkeypatch,
    degradation,
    recovery,
) -> None:
    monkeypatch.delenv(
        "STREAM_HEALTH_SRT_DEGRADATION_SECONDS",
        raising=False,
    )
    monkeypatch.delenv(
        "STREAM_HEALTH_SRT_RECOVERY_SECONDS",
        raising=False,
    )

    if degradation is not None:
        monkeypatch.setenv(
            "STREAM_HEALTH_SRT_DEGRADATION_SECONDS",
            degradation,
        )

    if recovery is not None:
        monkeypatch.setenv(
            "STREAM_HEALTH_SRT_RECOVERY_SECONDS",
            recovery,
        )

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    (
        "variable",
        "value",
    ),
    (
        (
            "STREAM_HEALTH_SRT_DEGRADATION_SECONDS",
            "-1",
        ),
        (
            "STREAM_HEALTH_SRT_RECOVERY_SECONDS",
            "-1",
        ),
    ),
)
def test_stream_health_temporal_policy_rejects_negative_values(
    monkeypatch,
    variable,
    value,
) -> None:
    monkeypatch.setenv(
        "STREAM_HEALTH_SRT_DEGRADATION_SECONDS",
        "0",
    )
    monkeypatch.setenv(
        "STREAM_HEALTH_SRT_RECOVERY_SECONDS",
        "0",
    )
    monkeypatch.setenv(variable, value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_stream_health_temporal_policy_accepts_zero_windows(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "STREAM_HEALTH_SRT_DEGRADATION_SECONDS",
        "0",
    )
    monkeypatch.setenv(
        "STREAM_HEALTH_SRT_RECOVERY_SECONDS",
        "0",
    )

    settings = Settings(_env_file=None)

    assert (
        settings.stream_health_srt_degradation_seconds
        == 0.0
    )
    assert (
        settings.stream_health_srt_recovery_seconds
        == 0.0
    )
