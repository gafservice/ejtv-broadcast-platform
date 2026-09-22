"""Normalize ffprobe stream evidence into the media observation contract.

This adapter is intentionally limited to descriptive video and audio
evidence. Physical process execution, GOP analysis, MPEG-TS structural
evidence, PCR evidence, Health, persistence, and runtime coordination
belong to later boundaries.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.domain.streaming.media_observation import (
    AudioTrackObservation,
    EvidenceAvailability,
    FrameRateObservation,
    InputMediaObservation,
    VideoTrackObservation,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


Probe = Callable[[str], dict[str, Any]]


class FFprobeMediaObserver:
    """Build one normalized media observation from ffprobe evidence."""

    def __init__(
        self,
        *,
        probe: Probe,
    ) -> None:
        if not callable(probe):
            raise TypeError("probe must be callable")

        self._probe = probe

    def observe(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        service_id: str,
        source: str,
        observed_at: datetime,
        path_name: str | None = None,
    ) -> InputMediaObservation:
        payload = self._probe(source)

        if not isinstance(payload, dict):
            raise TypeError("probe must return a dict")

        if "streams" not in payload:
            raise ValueError(
                "ffprobe payload must contain streams"
            )

        streams = payload["streams"]

        if not isinstance(streams, list):
            raise TypeError("ffprobe streams must be a list")

        video_stream = self._first_stream(
            streams,
            "video",
        )
        audio_stream = self._first_stream(
            streams,
            "audio",
        )

        video = self._build_video(video_stream)
        audio = self._build_audio(audio_stream)

        return InputMediaObservation(
            node_id=node_id,
            instance_id=instance_id,
            service_id=service_id,
            path_name=path_name,
            observed_at=observed_at,
            container=None,
            video=video,
            audio=audio,
        )

    @staticmethod
    def _first_stream(
        streams: list[Any],
        codec_type: str,
    ) -> dict[str, Any] | None:
        for stream in streams:
            if (
                isinstance(stream, dict)
                and stream.get("codec_type") == codec_type
            ):
                return stream

        return None

    @classmethod
    def _build_video(
        cls,
        stream: dict[str, Any] | None,
    ) -> VideoTrackObservation:
        if stream is None:
            return VideoTrackObservation(
                availability=EvidenceAvailability.UNAVAILABLE,
            )

        return VideoTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            codec=cls._optional_string(
                stream.get("codec_name")
            ),
            profile=cls._optional_string(
                stream.get("profile")
            ),
            level=cls._optional_string(
                stream.get("level")
            ),
            width=cls._optional_positive_int(
                stream.get("width")
            ),
            height=cls._optional_positive_int(
                stream.get("height")
            ),
            frame_rate=cls._frame_rate(
                stream.get("avg_frame_rate")
            ),
            gop=None,
        )

    @classmethod
    def _build_audio(
        cls,
        stream: dict[str, Any] | None,
    ) -> AudioTrackObservation:
        if stream is None:
            return AudioTrackObservation(
                availability=EvidenceAvailability.UNAVAILABLE,
            )

        return AudioTrackObservation(
            availability=EvidenceAvailability.AVAILABLE,
            codec=cls._optional_string(
                stream.get("codec_name")
            ),
            profile=cls._optional_string(
                stream.get("profile")
            ),
            sample_rate=cls._optional_positive_int(
                stream.get("sample_rate")
            ),
            channels=cls._optional_positive_int(
                stream.get("channels")
            ),
            channel_layout=cls._optional_string(
                stream.get("channel_layout")
            ),
        )

    @staticmethod
    def _optional_string(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        text = str(value).strip()

        return text or None

    @staticmethod
    def _optional_positive_int(
        value: object,
    ) -> int | None:
        if value is None or isinstance(value, bool):
            return None

        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None

        if parsed <= 0:
            return None

        return parsed

    @staticmethod
    def _frame_rate(
        value: object,
    ) -> FrameRateObservation | None:
        if not isinstance(value, str):
            return None

        parts = value.strip().split("/")

        if len(parts) != 2:
            return None

        try:
            numerator = int(parts[0])
            denominator = int(parts[1])
        except ValueError:
            return None

        if numerator <= 0 or denominator <= 0:
            return None

        return FrameRateObservation(
            numerator=numerator,
            denominator=denominator,
        )
