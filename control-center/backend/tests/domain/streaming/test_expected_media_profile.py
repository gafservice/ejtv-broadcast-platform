"""ENG-013C Contract 2 expected-media-profile domain tests."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.streaming.expected_media_profile import (
    ExpectedAudioProfile,
    ExpectedContainerProfile,
    ExpectedMediaProfile,
    ExpectedVideoProfile,
    MediaPresenceExpectation,
)


def test_presence_expectation_has_explicit_domain_values() -> None:
    assert MediaPresenceExpectation.REQUIRED.value == "required"
    assert MediaPresenceExpectation.OPTIONAL.value == "optional"
    assert MediaPresenceExpectation.FORBIDDEN.value == "forbidden"


def test_expected_container_profile_preserves_format_expectation() -> None:
    profile = ExpectedContainerProfile(
        presence=MediaPresenceExpectation.REQUIRED,
        container_type="mpegts",
    )

    assert profile.presence is MediaPresenceExpectation.REQUIRED
    assert profile.container_type == "mpegts"


def test_expected_video_profile_preserves_descriptive_expectations() -> None:
    profile = ExpectedVideoProfile(
        presence=MediaPresenceExpectation.REQUIRED,
        codec="h264",
        profile="High",
        level="4.1",
        width=1920,
        height=1080,
        frame_rate_numerator=30000,
        frame_rate_denominator=1001,
        gop_interval_seconds=2.0,
    )

    assert profile.presence is MediaPresenceExpectation.REQUIRED
    assert profile.codec == "h264"
    assert profile.profile == "High"
    assert profile.level == "4.1"
    assert profile.width == 1920
    assert profile.height == 1080
    assert profile.frame_rate_numerator == 30000
    assert profile.frame_rate_denominator == 1001
    assert profile.gop_interval_seconds == pytest.approx(2.0)


def test_expected_audio_profile_preserves_descriptive_expectations() -> None:
    profile = ExpectedAudioProfile(
        presence=MediaPresenceExpectation.REQUIRED,
        codec="aac",
        profile="LC",
        sample_rate=48000,
        channels=2,
        channel_layout="stereo",
    )

    assert profile.presence is MediaPresenceExpectation.REQUIRED
    assert profile.codec == "aac"
    assert profile.profile == "LC"
    assert profile.sample_rate == 48000
    assert profile.channels == 2
    assert profile.channel_layout == "stereo"


def test_expected_media_profile_preserves_service_identity_and_components() -> None:
    container = ExpectedContainerProfile(
        presence=MediaPresenceExpectation.REQUIRED,
        container_type="mpegts",
    )

    video = ExpectedVideoProfile(
        presence=MediaPresenceExpectation.REQUIRED,
        codec="h264",
    )

    audio = ExpectedAudioProfile(
        presence=MediaPresenceExpectation.REQUIRED,
        codec="aac",
    )

    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name="impact",
        container=container,
        video=video,
        audio=audio,
    )

    assert profile.profile_id == "impact-main"
    assert profile.service_id == "impact"
    assert profile.path_name == "impact"

    assert profile.container is container
    assert profile.video is video
    assert profile.audio is audio


def test_expected_media_profile_allows_absent_path_name() -> None:
    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
        path_name=None,
    )

    assert profile.path_name is None


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("profile_id", ""),
        ("profile_id", "   "),
        ("service_id", ""),
        ("service_id", "   "),
        ("path_name", ""),
        ("path_name", "   "),
    ],
)
def test_expected_media_profile_rejects_blank_identity(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "profile_id": "impact-main",
        "service_id": "impact",
        "path_name": "impact",
    }

    kwargs[field_name] = value

    with pytest.raises(ValueError):
        ExpectedMediaProfile(**kwargs)


def test_expected_media_profile_normalizes_identity() -> None:
    profile = ExpectedMediaProfile(
        profile_id="  impact-main  ",
        service_id="  impact  ",
        path_name="  impact  ",
    )

    assert profile.profile_id == "impact-main"
    assert profile.service_id == "impact"
    assert profile.path_name == "impact"


@pytest.mark.parametrize(
    "profile_type",
    [
        ExpectedContainerProfile,
        ExpectedVideoProfile,
        ExpectedAudioProfile,
    ],
)
def test_expected_component_profiles_require_presence_enum(
    profile_type: type,
) -> None:
    with pytest.raises(TypeError):
        profile_type(
            presence="required",
        )


def test_expected_video_frame_rate_preserves_rational_form() -> None:
    profile = ExpectedVideoProfile(
        presence=MediaPresenceExpectation.REQUIRED,
        frame_rate_numerator=30000,
        frame_rate_denominator=1001,
    )

    assert (
        profile.frame_rate_numerator,
        profile.frame_rate_denominator,
    ) == (30000, 1001)


def test_expected_video_rejects_incomplete_frame_rate() -> None:
    with pytest.raises(ValueError):
        ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            frame_rate_numerator=30000,
            frame_rate_denominator=None,
        )


def test_expected_video_rejects_non_positive_frame_rate_denominator() -> None:
    with pytest.raises(ValueError):
        ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            frame_rate_numerator=30000,
            frame_rate_denominator=0,
        )


def test_expected_media_profile_has_no_health_state() -> None:
    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
    )

    assert not hasattr(profile, "health")
    assert not hasattr(profile, "status")


def test_expected_media_profile_has_no_node_runtime_identity() -> None:
    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
    )

    assert not hasattr(profile, "node_id")
    assert not hasattr(profile, "instance_id")


def test_expected_media_profile_is_immutable() -> None:
    profile = ExpectedMediaProfile(
        profile_id="impact-main",
        service_id="impact",
    )

    with pytest.raises(FrozenInstanceError):
        profile.service_id = "ejtv"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("width", 0),
        ("width", -1),
        ("height", 0),
        ("height", -1),
        ("frame_rate_numerator", 0),
        ("frame_rate_numerator", -1),
        ("frame_rate_denominator", 0),
        ("frame_rate_denominator", -1),
    ],
)
def test_expected_video_rejects_non_positive_integer_expectations(
    field_name: str,
    value: int,
) -> None:
    kwargs = {
        "presence": MediaPresenceExpectation.REQUIRED,
    }

    if field_name.startswith("frame_rate_"):
        kwargs["frame_rate_numerator"] = 30000
        kwargs["frame_rate_denominator"] = 1001

    kwargs[field_name] = value

    with pytest.raises(ValueError):
        ExpectedVideoProfile(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("width", True),
        ("height", True),
        ("frame_rate_numerator", True),
        ("frame_rate_denominator", True),
    ],
)
def test_expected_video_rejects_boolean_integer_expectations(
    field_name: str,
    value: bool,
) -> None:
    kwargs = {
        "presence": MediaPresenceExpectation.REQUIRED,
    }

    if field_name.startswith("frame_rate_"):
        kwargs["frame_rate_numerator"] = 30000
        kwargs["frame_rate_denominator"] = 1001

    kwargs[field_name] = value

    with pytest.raises(TypeError):
        ExpectedVideoProfile(**kwargs)


@pytest.mark.parametrize(
    "value",
    [
        0,
        -0.1,
        -1,
    ],
)
def test_expected_video_rejects_non_positive_gop_interval(
    value: float,
) -> None:
    with pytest.raises(ValueError):
        ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            gop_interval_seconds=value,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        "2.0",
    ],
)
def test_expected_video_rejects_non_numeric_gop_interval(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        ExpectedVideoProfile(
            presence=MediaPresenceExpectation.REQUIRED,
            gop_interval_seconds=value,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("sample_rate", 0),
        ("sample_rate", -1),
        ("channels", 0),
        ("channels", -1),
    ],
)
def test_expected_audio_rejects_non_positive_integer_expectations(
    field_name: str,
    value: int,
) -> None:
    kwargs = {
        "presence": MediaPresenceExpectation.REQUIRED,
        field_name: value,
    }

    with pytest.raises(ValueError):
        ExpectedAudioProfile(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    [
        "sample_rate",
        "channels",
    ],
)
def test_expected_audio_rejects_boolean_integer_expectations(
    field_name: str,
) -> None:
    kwargs = {
        "presence": MediaPresenceExpectation.REQUIRED,
        field_name: True,
    }

    with pytest.raises(TypeError):
        ExpectedAudioProfile(**kwargs)


@pytest.mark.parametrize(
    ("profile_type", "field_name"),
    [
        (ExpectedContainerProfile, "container_type"),
        (ExpectedVideoProfile, "codec"),
        (ExpectedVideoProfile, "profile"),
        (ExpectedVideoProfile, "level"),
        (ExpectedAudioProfile, "codec"),
        (ExpectedAudioProfile, "profile"),
        (ExpectedAudioProfile, "channel_layout"),
    ],
)
def test_expected_component_profiles_reject_blank_descriptive_text(
    profile_type: type,
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        profile_type(
            presence=MediaPresenceExpectation.REQUIRED,
            **{field_name: "   "},
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("container", object()),
        ("video", object()),
        ("audio", object()),
    ],
)
def test_expected_media_profile_rejects_invalid_component_types(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        "profile_id": "impact-main",
        "service_id": "impact",
        field_name: value,
    }

    with pytest.raises(TypeError):
        ExpectedMediaProfile(**kwargs)
