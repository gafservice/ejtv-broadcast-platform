"""ENG-013C Slice 4 video-track and GOP observation contract tests."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.streaming.media_observation import (
    EvidenceAvailability,
    FrameRateObservation,
    GOPObservation,
    VideoTrackObservation,
)


# ---------------------------------------------------------------------------
# FrameRateObservation
# ---------------------------------------------------------------------------


def test_frame_rate_preserves_rational_evidence() -> None:
    frame_rate = FrameRateObservation(
        numerator=30000,
        denominator=1001,
    )

    assert frame_rate.numerator == 30000
    assert frame_rate.denominator == 1001


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("numerator", 29.97),
        ("numerator", True),
        ("denominator", 1001.0),
        ("denominator", False),
    ],
)
def test_frame_rate_requires_integer_components(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        "numerator": 30000,
        "denominator": 1001,
    }
    kwargs[field_name] = value

    with pytest.raises(TypeError):
        FrameRateObservation(**kwargs)


def test_frame_rate_rejects_negative_numerator() -> None:
    with pytest.raises(ValueError):
        FrameRateObservation(
            numerator=-1,
            denominator=1001,
        )


@pytest.mark.parametrize("denominator", [0, -1])
def test_frame_rate_requires_positive_denominator(
    denominator: int,
) -> None:
    with pytest.raises(ValueError):
        FrameRateObservation(
            numerator=30000,
            denominator=denominator,
        )


def test_frame_rate_is_immutable() -> None:
    frame_rate = FrameRateObservation(
        numerator=30000,
        denominator=1001,
    )

    with pytest.raises(FrozenInstanceError):
        frame_rate.numerator = 25  # type: ignore[misc]


# ---------------------------------------------------------------------------
# GOPObservation
# ---------------------------------------------------------------------------


def make_gop(**overrides: object) -> GOPObservation:
    values: dict[str, object] = {
        "availability": EvidenceAvailability.AVAILABLE,
        "observed_frame_count": 3588,
        "keyframe_count": 55,
        "i_frame_count": 55,
        "p_frame_count": 3533,
        "b_frame_count": 0,
        "interval_count": 54,
        "minimum_interval": 2.001989,
        "maximum_interval": 6.006,
        "average_interval": 2.187371,
        "median_interval": 2.002,
        "minimum_frames_per_interval": 60,
        "maximum_frames_per_interval": 178,
        "average_frames_per_interval": 65.333333,
        "median_frames_per_interval": 60.0,
    }
    values.update(overrides)
    return GOPObservation(**values)


def test_gop_preserves_observed_distribution_evidence() -> None:
    gop = make_gop()

    assert gop.availability is EvidenceAvailability.AVAILABLE
    assert gop.observed_frame_count == 3588
    assert gop.keyframe_count == 55

    assert gop.i_frame_count == 55
    assert gop.p_frame_count == 3533
    assert gop.b_frame_count == 0

    assert gop.interval_count == 54

    assert gop.minimum_interval == pytest.approx(2.001989)
    assert gop.maximum_interval == pytest.approx(6.006)
    assert gop.average_interval == pytest.approx(2.187371)
    assert gop.median_interval == pytest.approx(2.002)

    assert gop.minimum_frames_per_interval == 60
    assert gop.maximum_frames_per_interval == 178
    assert gop.average_frames_per_interval == pytest.approx(65.333333)
    assert gop.median_frames_per_interval == pytest.approx(60.0)


@pytest.mark.parametrize(
    "availability",
    list(EvidenceAvailability),
)
def test_gop_supports_every_evidence_availability(
    availability: EvidenceAvailability,
) -> None:
    gop = GOPObservation(
        availability=availability,
    )

    assert gop.availability is availability


def test_gop_rejects_non_availability_value() -> None:
    with pytest.raises(TypeError):
        GOPObservation(
            availability="AVAILABLE",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "observed_frame_count",
        "keyframe_count",
        "i_frame_count",
        "p_frame_count",
        "b_frame_count",
        "interval_count",
    ],
)
def test_gop_rejects_negative_counts(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_gop(**{field_name: -1})


@pytest.mark.parametrize(
    "field_name",
    [
        "observed_frame_count",
        "keyframe_count",
        "i_frame_count",
        "p_frame_count",
        "b_frame_count",
        "interval_count",
    ],
)
@pytest.mark.parametrize(
    "value",
    [1.5, True],
)
def test_gop_counts_require_integers(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(TypeError):
        make_gop(**{field_name: value})


@pytest.mark.parametrize(
    "field_name",
    [
        "minimum_interval",
        "maximum_interval",
        "average_interval",
        "median_interval",
        "minimum_frames_per_interval",
        "maximum_frames_per_interval",
        "average_frames_per_interval",
        "median_frames_per_interval",
    ],
)
def test_gop_rejects_negative_statistical_evidence(
    field_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_gop(**{field_name: -0.1})


@pytest.mark.parametrize(
    "field_name",
    [
        "minimum_interval",
        "maximum_interval",
        "average_interval",
        "median_interval",
        "minimum_frames_per_interval",
        "maximum_frames_per_interval",
        "average_frames_per_interval",
        "median_frames_per_interval",
    ],
)
@pytest.mark.parametrize(
    "value",
    ["2.0", True],
)
def test_gop_statistical_evidence_requires_numbers(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(TypeError):
        make_gop(**{field_name: value})


def test_gop_rejects_reversed_interval_range() -> None:
    with pytest.raises(ValueError):
        make_gop(
            minimum_interval=6.0,
            maximum_interval=2.0,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("average_interval", 1.0),
        ("median_interval", 1.0),
        ("average_interval", 7.0),
        ("median_interval", 7.0),
    ],
)
def test_gop_interval_center_statistics_must_be_inside_range(
    field_name: str,
    value: float,
) -> None:
    with pytest.raises(ValueError):
        make_gop(**{field_name: value})


def test_gop_rejects_reversed_frames_per_interval_range() -> None:
    with pytest.raises(ValueError):
        make_gop(
            minimum_frames_per_interval=180,
            maximum_frames_per_interval=60,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("average_frames_per_interval", 50),
        ("median_frames_per_interval", 50),
        ("average_frames_per_interval", 200),
        ("median_frames_per_interval", 200),
    ],
)
def test_gop_frames_per_interval_center_statistics_must_be_inside_range(
    field_name: str,
    value: float,
) -> None:
    with pytest.raises(ValueError):
        make_gop(**{field_name: value})


def test_gop_does_not_require_statistics_when_evidence_is_insufficient() -> None:
    gop = GOPObservation(
        availability=EvidenceAvailability.INSUFFICIENT,
        observed_frame_count=30,
        keyframe_count=1,
        i_frame_count=1,
        p_frame_count=29,
        b_frame_count=0,
        interval_count=0,
    )

    assert gop.minimum_interval is None
    assert gop.maximum_interval is None
    assert gop.average_interval is None
    assert gop.median_interval is None

    assert gop.minimum_frames_per_interval is None
    assert gop.maximum_frames_per_interval is None
    assert gop.average_frames_per_interval is None
    assert gop.median_frames_per_interval is None


def test_gop_is_immutable() -> None:
    gop = make_gop()

    with pytest.raises(FrozenInstanceError):
        gop.maximum_interval = 2.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# VideoTrackObservation integration
# ---------------------------------------------------------------------------


def test_video_track_preserves_descriptive_and_gop_evidence() -> None:
    frame_rate = FrameRateObservation(
        numerator=30000,
        denominator=1001,
    )
    gop = make_gop()

    video = VideoTrackObservation(
        availability=EvidenceAvailability.AVAILABLE,
        codec="hevc",
        profile="Main",
        level="4",
        width=1920,
        height=1080,
        frame_rate=frame_rate,
        gop=gop,
    )

    assert video.codec == "hevc"
    assert video.profile == "Main"
    assert video.level == "4"
    assert video.width == 1920
    assert video.height == 1080
    assert video.frame_rate is frame_rate
    assert video.gop is gop


@pytest.mark.parametrize(
    "field_name",
    [
        "codec",
        "profile",
        "level",
    ],
)
def test_video_track_rejects_blank_descriptive_strings(
    field_name: str,
) -> None:
    kwargs: dict[str, object] = {
        "availability": EvidenceAvailability.AVAILABLE,
    }
    kwargs[field_name] = "   "

    with pytest.raises(ValueError):
        VideoTrackObservation(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    ["width", "height"],
)
def test_video_track_rejects_non_positive_dimensions(
    field_name: str,
) -> None:
    kwargs: dict[str, object] = {
        "availability": EvidenceAvailability.AVAILABLE,
        field_name: 0,
    }

    with pytest.raises(ValueError):
        VideoTrackObservation(**kwargs)


@pytest.mark.parametrize(
    "field_name",
    ["width", "height"],
)
@pytest.mark.parametrize(
    "value",
    [1920.0, True],
)
def test_video_track_dimensions_require_integers(
    field_name: str,
    value: object,
) -> None:
    kwargs: dict[str, object] = {
        "availability": EvidenceAvailability.AVAILABLE,
        field_name: value,
    }

    with pytest.raises(TypeError):
        VideoTrackObservation(**kwargs)


def test_video_track_rejects_non_frame_rate_object() -> None:
    with pytest.raises(TypeError):
        VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            frame_rate=29.97,  # type: ignore[arg-type]
        )


def test_video_track_rejects_non_gop_object() -> None:
    with pytest.raises(TypeError):
        VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            gop=2.0,  # type: ignore[arg-type]
        )


def test_video_track_allows_absent_optional_evidence() -> None:
    video = VideoTrackObservation(
        availability=EvidenceAvailability.UNAVAILABLE,
    )

    assert video.codec is None
    assert video.profile is None
    assert video.level is None
    assert video.width is None
    assert video.height is None
    assert video.frame_rate is None
    assert video.gop is None


def test_video_track_is_immutable() -> None:
    video = VideoTrackObservation(
        availability=EvidenceAvailability.AVAILABLE,
        codec="hevc",
    )

    with pytest.raises(FrozenInstanceError):
        video.codec = "h264"  # type: ignore[misc]
