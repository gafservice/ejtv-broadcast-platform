from datetime import datetime, timezone

from app.adapters.media.ffprobe_media_observer import (
    FFprobeMediaObserver,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
    FrameRateObservation,
    InputMediaObservation,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


OBSERVED_AT = datetime(
    2026,
    9,
    22,
    8,
    0,
    tzinfo=timezone.utc,
)


def make_node_id() -> NodeId:
    return NodeId(
        id="ejtv-01",
        name="ejtv-01",
        display_name="EJTV 01",
        created_at=OBSERVED_AT,
    )


def test_observer_normalizes_ffprobe_stream_evidence() -> None:
    probe_payload = {
        "streams": [
            {
                "index": 0,
                "codec_name": "h264",
                "profile": "Main",
                "level": 40,
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "30/1",
                "codec_type": "video",
            },
            {
                "index": 1,
                "codec_name": "aac",
                "profile": "LC",
                "sample_rate": "48000",
                "channels": 2,
                "channel_layout": "stereo",
                "codec_type": "audio",
            },
        ]
    }

    observer = FFprobeMediaObserver(
        probe=lambda _: probe_payload,
    )

    result = observer.observe(
        node_id=make_node_id(),
        instance_id=NodeInstanceId("ejtv-01-runtime"),
        service_id="impact",
        path_name="impact",
        source="rtsp://127.0.0.1:8554/impact",
        observed_at=OBSERVED_AT,
    )

    assert isinstance(result, InputMediaObservation)

    assert result.node_id == make_node_id()
    assert result.instance_id == NodeInstanceId(
        "ejtv-01-runtime"
    )
    assert result.service_id == "impact"
    assert result.path_name == "impact"
    assert result.observed_at == OBSERVED_AT

    assert result.container is None

    assert result.video is not None
    assert (
        result.video.availability
        is EvidenceAvailability.AVAILABLE
    )
    assert result.video.codec == "h264"
    assert result.video.profile == "Main"
    assert result.video.level == "40"
    assert result.video.width == 1920
    assert result.video.height == 1080
    assert result.video.frame_rate == FrameRateObservation(
        numerator=30,
        denominator=1,
    )
    assert result.video.gop is None

    assert result.audio is not None
    assert (
        result.audio.availability
        is EvidenceAvailability.AVAILABLE
    )
    assert result.audio.codec == "aac"
    assert result.audio.profile == "LC"
    assert result.audio.sample_rate == 48000
    assert result.audio.channels == 2
    assert result.audio.channel_layout == "stereo"


def make_observer(payload):
    return FFprobeMediaObserver(
        probe=lambda _: payload,
    )


def observe_with(observer):
    return observer.observe(
        node_id=make_node_id(),
        instance_id=NodeInstanceId("ejtv-01-runtime"),
        service_id="impact",
        path_name="impact",
        source="rtsp://127.0.0.1:8554/impact",
        observed_at=OBSERVED_AT,
    )


def test_successful_probe_without_video_marks_video_unavailable() -> None:
    result = observe_with(
        make_observer(
            {
                "streams": [
                    {
                        "codec_type": "audio",
                        "codec_name": "aac",
                    },
                ],
            }
        )
    )

    assert result.video is not None
    assert (
        result.video.availability
        is EvidenceAvailability.UNAVAILABLE
    )


def test_present_video_with_partial_fields_remains_available() -> None:
    result = observe_with(
        make_observer(
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "avg_frame_rate": "0/0",
                    },
                ],
            }
        )
    )

    assert result.video is not None
    assert (
        result.video.availability
        is EvidenceAvailability.AVAILABLE
    )
    assert result.video.codec == "h264"
    assert result.video.frame_rate is None


def test_payload_without_streams_is_not_observed_absence() -> None:
    observer = make_observer({})

    try:
        observe_with(observer)
    except ValueError as exc:
        assert "streams" in str(exc)
    else:
        raise AssertionError(
            "missing streams evidence must not become UNAVAILABLE"
        )


def test_probe_failure_is_not_converted_to_track_absence() -> None:
    def failing_probe(_):
        raise TimeoutError("ffprobe timed out")

    observer = FFprobeMediaObserver(
        probe=failing_probe,
    )

    try:
        observe_with(observer)
    except TimeoutError as exc:
        assert str(exc) == "ffprobe timed out"
    else:
        raise AssertionError(
            "probe failure must propagate"
        )
