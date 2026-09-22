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


def test_media_observation_rtsp_base_url_has_local_default() -> None:
    settings = Settings(_env_file=None)

    assert (
        settings.media_observation_rtsp_base_url
        == "rtsp://127.0.0.1:8554"
    )


def test_media_observation_rtsp_base_url_can_be_configured(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "MEDIA_OBSERVATION_RTSP_BASE_URL",
        "rtsp://media-node.internal:9554",
    )

    settings = Settings(_env_file=None)

    assert (
        settings.media_observation_rtsp_base_url
        == "rtsp://media-node.internal:9554"
    )


def test_media_health_temporal_policy_has_operational_defaults(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "MEDIA_HEALTH_DEGRADATION_SECONDS",
        raising=False,
    )
    monkeypatch.delenv(
        "MEDIA_HEALTH_RECOVERY_SECONDS",
        raising=False,
    )

    settings = Settings(_env_file=None)

    assert settings.media_health_degradation_seconds == 10.0
    assert settings.media_health_recovery_seconds == 5.0


def test_media_health_temporal_policy_can_be_configured(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "MEDIA_HEALTH_DEGRADATION_SECONDS",
        "7.5",
    )
    monkeypatch.setenv(
        "MEDIA_HEALTH_RECOVERY_SECONDS",
        "12.0",
    )

    settings = Settings(_env_file=None)

    assert settings.media_health_degradation_seconds == 7.5
    assert settings.media_health_recovery_seconds == 12.0


@pytest.mark.parametrize(
    (
        "variable",
        "value",
    ),
    (
        (
            "MEDIA_HEALTH_DEGRADATION_SECONDS",
            "-1",
        ),
        (
            "MEDIA_HEALTH_RECOVERY_SECONDS",
            "-1",
        ),
    ),
)
def test_media_health_temporal_policy_rejects_negative_values(
    monkeypatch,
    variable,
    value,
) -> None:
    monkeypatch.setenv(
        "MEDIA_HEALTH_DEGRADATION_SECONDS",
        "10",
    )
    monkeypatch.setenv(
        "MEDIA_HEALTH_RECOVERY_SECONDS",
        "5",
    )
    monkeypatch.setenv(
        variable,
        value,
    )

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_media_health_temporal_policy_accepts_zero_windows(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "MEDIA_HEALTH_DEGRADATION_SECONDS",
        "0",
    )
    monkeypatch.setenv(
        "MEDIA_HEALTH_RECOVERY_SECONDS",
        "0",
    )

    settings = Settings(_env_file=None)

    assert settings.media_health_degradation_seconds == 0.0
    assert settings.media_health_recovery_seconds == 0.0


def test_media_observation_interval_defaults_to_five_seconds(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "MEDIA_OBSERVATION_INTERVAL_SECONDS",
        raising=False,
    )

    settings = Settings(_env_file=None)

    assert (
        settings.media_observation_interval_seconds
        == 5.0
    )


def test_media_observation_interval_accepts_environment_override(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "MEDIA_OBSERVATION_INTERVAL_SECONDS",
        "7.5",
    )

    settings = Settings(_env_file=None)

    assert (
        settings.media_observation_interval_seconds
        == 7.5
    )


def test_media_observation_interval_rejects_zero(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "MEDIA_OBSERVATION_INTERVAL_SECONDS",
        "0",
    )

    with pytest.raises(
        ValidationError,
    ):
        Settings(_env_file=None)


def test_media_observation_interval_rejects_negative_value(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "MEDIA_OBSERVATION_INTERVAL_SECONDS",
        "-1",
    )

    with pytest.raises(
        ValidationError,
    ):
        Settings(_env_file=None)
