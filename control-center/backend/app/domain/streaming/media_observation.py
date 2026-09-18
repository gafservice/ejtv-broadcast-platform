"""Input media observation domain.

ENG-013C — Media / Track Health

This module defines normalized evidence observed from multimedia input.

Observation is intentionally separate from expectation and Health.
No Health classification, thresholds, alarms, events or temporal
stabilization belong in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


class EvidenceAvailability(str, Enum):
    """Availability of evidence independently from Health."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    INSUFFICIENT = "insufficient"
    NOT_APPLICABLE = "not_applicable"


def _validate_mpegts_pid(pid: int, field_name: str) -> None:
    """Validate an MPEG-TS 13-bit PID."""

    if not isinstance(pid, int) or isinstance(pid, bool):
        raise TypeError(f"{field_name} must be an int")

    if not 0 <= pid <= 0x1FFF:
        raise ValueError(
            f"{field_name} must be in MPEG-TS PID range 0..0x1FFF"
        )


def _validate_non_negative_int(value: int, field_name: str) -> None:
    """Validate a non-negative integer evidence counter."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be an int")

    if value < 0:
        raise ValueError(f"{field_name} must not be negative")


def _validate_optional_version(
    value: int | None,
    field_name: str,
) -> None:
    """Validate an optional MPEG-TS PSI version number."""

    if value is None:
        return

    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be an int or None")

    if not 0 <= value <= 31:
        raise ValueError(
            f"{field_name} must be in MPEG-TS version range 0..31"
        )


@dataclass(frozen=True, slots=True)
class MPEGTSStreamObservation:
    """Observed MPEG-TS elementary-stream topology."""

    pid: int
    stream_type: int

    def __post_init__(self) -> None:
        _validate_mpegts_pid(self.pid, "MPEGTSStreamObservation.pid")

        if (
            not isinstance(self.stream_type, int)
            or isinstance(self.stream_type, bool)
        ):
            raise TypeError(
                "MPEGTSStreamObservation.stream_type must be an int"
            )

        if not 0 <= self.stream_type <= 0xFF:
            raise ValueError(
                "MPEGTSStreamObservation.stream_type must be "
                "in range 0..0xFF"
            )


@dataclass(frozen=True, slots=True)
class PCRObservation:
    """Observed sender-PCR clock evidence for one MPEG-TS program."""

    availability: EvidenceAvailability
    pid: int
    sample_count: int

    first_pcr: float | None = None
    last_pcr: float | None = None
    pcr_span: float | None = None

    minimum_delta: float | None = None
    maximum_delta: float | None = None
    average_delta: float | None = None
    median_delta: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "PCRObservation.availability must be "
                "EvidenceAvailability"
            )

        _validate_mpegts_pid(
            self.pid,
            "PCRObservation.pid",
        )

        _validate_non_negative_int(
            self.sample_count,
            "PCRObservation.sample_count",
        )

        temporal_fields = (
            "first_pcr",
            "last_pcr",
            "pcr_span",
            "minimum_delta",
            "maximum_delta",
            "average_delta",
            "median_delta",
        )

        for field_name in temporal_fields:
            value = getattr(self, field_name)

            if value is None:
                continue

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                raise TypeError(
                    f"PCRObservation.{field_name} must be "
                    "a number or None"
                )

            if value < 0:
                raise ValueError(
                    f"PCRObservation.{field_name} must not be negative"
                )

        if (
            self.minimum_delta is not None
            and self.maximum_delta is not None
            and self.minimum_delta > self.maximum_delta
        ):
            raise ValueError(
                "PCRObservation.minimum_delta must not exceed "
                "maximum_delta"
            )

        if (
            self.average_delta is not None
            and self.minimum_delta is not None
            and self.average_delta < self.minimum_delta
        ):
            raise ValueError(
                "PCRObservation.average_delta must not be below "
                "minimum_delta"
            )

        if (
            self.average_delta is not None
            and self.maximum_delta is not None
            and self.average_delta > self.maximum_delta
        ):
            raise ValueError(
                "PCRObservation.average_delta must not exceed "
                "maximum_delta"
            )

        if (
            self.median_delta is not None
            and self.minimum_delta is not None
            and self.median_delta < self.minimum_delta
        ):
            raise ValueError(
                "PCRObservation.median_delta must not be below "
                "minimum_delta"
            )

        if (
            self.median_delta is not None
            and self.maximum_delta is not None
            and self.median_delta > self.maximum_delta
        ):
            raise ValueError(
                "PCRObservation.median_delta must not exceed "
                "maximum_delta"
            )


@dataclass(frozen=True, slots=True)
class MPEGTSProgramObservation:
    """Observed MPEG-TS program topology."""

    program_number: int
    pmt_pid: int
    pcr_pid: int
    streams: tuple[MPEGTSStreamObservation, ...]
    pcr: PCRObservation | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.program_number, int)
            or isinstance(self.program_number, bool)
        ):
            raise TypeError(
                "MPEGTSProgramObservation.program_number must be an int"
            )

        if not 0 <= self.program_number <= 0xFFFF:
            raise ValueError(
                "MPEGTSProgramObservation.program_number must be "
                "in range 0..0xFFFF"
            )

        _validate_mpegts_pid(
            self.pmt_pid,
            "MPEGTSProgramObservation.pmt_pid",
        )
        _validate_mpegts_pid(
            self.pcr_pid,
            "MPEGTSProgramObservation.pcr_pid",
        )

        if not isinstance(self.streams, tuple):
            raise TypeError(
                "MPEGTSProgramObservation.streams must be a tuple"
            )

        if not all(
            isinstance(stream, MPEGTSStreamObservation)
            for stream in self.streams
        ):
            raise TypeError(
                "MPEGTSProgramObservation.streams must contain only "
                "MPEGTSStreamObservation objects"
            )

        if self.pcr is not None:
            if not isinstance(self.pcr, PCRObservation):
                raise TypeError(
                    "MPEGTSProgramObservation.pcr must be "
                    "PCRObservation or None"
                )

            if self.pcr.pid != self.pcr_pid:
                raise ValueError(
                    "MPEGTSProgramObservation.pcr.pid must match "
                    "pcr_pid"
                )


@dataclass(frozen=True, slots=True)
class MPEGTSObservation:
    """Observed MPEG-TS structural and transport-integrity evidence."""

    availability: EvidenceAvailability

    transport_stream_id: int | None = None
    pat_present: bool | None = None
    pat_version: int | None = None
    pmt_present: bool | None = None
    pmt_version: int | None = None

    transport_packet_count: int = 0
    sync_error_count: int = 0
    malformed_packet_count: int = 0
    transport_error_indicator_count: int = 0
    continuity_check_count: int = 0
    continuity_error_count: int = 0
    discontinuity_indicator_count: int = 0

    programs: tuple[MPEGTSProgramObservation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "MPEGTSObservation.availability must be "
                "EvidenceAvailability"
            )

        if self.transport_stream_id is not None:
            if (
                not isinstance(self.transport_stream_id, int)
                or isinstance(self.transport_stream_id, bool)
            ):
                raise TypeError(
                    "MPEGTSObservation.transport_stream_id must "
                    "be an int or None"
                )

            if not 0 <= self.transport_stream_id <= 0xFFFF:
                raise ValueError(
                    "MPEGTSObservation.transport_stream_id must "
                    "be in range 0..0xFFFF"
                )

        for field_name in ("pat_present", "pmt_present"):
            value = getattr(self, field_name)

            if value is not None and not isinstance(value, bool):
                raise TypeError(
                    f"MPEGTSObservation.{field_name} must be "
                    "a bool or None"
                )

        _validate_optional_version(
            self.pat_version,
            "MPEGTSObservation.pat_version",
        )
        _validate_optional_version(
            self.pmt_version,
            "MPEGTSObservation.pmt_version",
        )

        counter_names = (
            "transport_packet_count",
            "sync_error_count",
            "malformed_packet_count",
            "transport_error_indicator_count",
            "continuity_check_count",
            "continuity_error_count",
            "discontinuity_indicator_count",
        )

        for field_name in counter_names:
            _validate_non_negative_int(
                getattr(self, field_name),
                f"MPEGTSObservation.{field_name}",
            )

        if self.continuity_error_count > self.continuity_check_count:
            raise ValueError(
                "MPEGTSObservation.continuity_error_count must not "
                "exceed continuity_check_count"
            )

        if not isinstance(self.programs, tuple):
            raise TypeError(
                "MPEGTSObservation.programs must be a tuple"
            )

        if not all(
            isinstance(program, MPEGTSProgramObservation)
            for program in self.programs
        ):
            raise TypeError(
                "MPEGTSObservation.programs must contain only "
                "MPEGTSProgramObservation objects"
            )


@dataclass(frozen=True, slots=True)
class ContainerObservation:
    """Generic container-level evidence."""

    availability: EvidenceAvailability
    container_type: str | None = None
    mpegts: MPEGTSObservation | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "ContainerObservation.availability must be "
                "EvidenceAvailability"
            )

        if self.container_type is not None:
            normalized = self.container_type.strip()

            if not normalized:
                raise ValueError(
                    "ContainerObservation.container_type must not "
                    "be blank when present"
                )

            object.__setattr__(
                self,
                "container_type",
                normalized,
            )

        if self.mpegts is not None and not isinstance(
            self.mpegts,
            MPEGTSObservation,
        ):
            raise TypeError(
                "ContainerObservation.mpegts must be "
                "MPEGTSObservation or None"
            )


@dataclass(frozen=True, slots=True)
class FrameRateObservation:
    """Observed rational video frame-rate evidence."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.numerator, int)
            or isinstance(self.numerator, bool)
        ):
            raise TypeError(
                "FrameRateObservation.numerator must be an int"
            )

        if (
            not isinstance(self.denominator, int)
            or isinstance(self.denominator, bool)
        ):
            raise TypeError(
                "FrameRateObservation.denominator must be an int"
            )

        if self.numerator < 0:
            raise ValueError(
                "FrameRateObservation.numerator must not be negative"
            )

        if self.denominator <= 0:
            raise ValueError(
                "FrameRateObservation.denominator must be positive"
            )


@dataclass(frozen=True, slots=True)
class GOPObservation:
    """Observed GOP and reported-keyframe distribution evidence."""

    availability: EvidenceAvailability

    observed_frame_count: int = 0
    keyframe_count: int = 0
    i_frame_count: int = 0
    p_frame_count: int = 0
    b_frame_count: int = 0
    interval_count: int = 0

    minimum_interval: float | None = None
    maximum_interval: float | None = None
    average_interval: float | None = None
    median_interval: float | None = None

    minimum_frames_per_interval: float | None = None
    maximum_frames_per_interval: float | None = None
    average_frames_per_interval: float | None = None
    median_frames_per_interval: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "GOPObservation.availability must be "
                "EvidenceAvailability"
            )

        count_fields = (
            "observed_frame_count",
            "keyframe_count",
            "i_frame_count",
            "p_frame_count",
            "b_frame_count",
            "interval_count",
        )

        for field_name in count_fields:
            _validate_non_negative_int(
                getattr(self, field_name),
                f"GOPObservation.{field_name}",
            )

        statistical_fields = (
            "minimum_interval",
            "maximum_interval",
            "average_interval",
            "median_interval",
            "minimum_frames_per_interval",
            "maximum_frames_per_interval",
            "average_frames_per_interval",
            "median_frames_per_interval",
        )

        for field_name in statistical_fields:
            value = getattr(self, field_name)

            if value is None:
                continue

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                raise TypeError(
                    f"GOPObservation.{field_name} must be "
                    "a number or None"
                )

            if value < 0:
                raise ValueError(
                    f"GOPObservation.{field_name} must not be negative"
                )

        self._validate_range(
            minimum=self.minimum_interval,
            maximum=self.maximum_interval,
            average=self.average_interval,
            median=self.median_interval,
            label="interval",
        )

        self._validate_range(
            minimum=self.minimum_frames_per_interval,
            maximum=self.maximum_frames_per_interval,
            average=self.average_frames_per_interval,
            median=self.median_frames_per_interval,
            label="frames_per_interval",
        )

    @staticmethod
    def _validate_range(
        *,
        minimum: float | None,
        maximum: float | None,
        average: float | None,
        median: float | None,
        label: str,
    ) -> None:
        if (
            minimum is not None
            and maximum is not None
            and minimum > maximum
        ):
            raise ValueError(
                f"GOPObservation minimum {label} must not exceed "
                f"maximum {label}"
            )

        if minimum is not None:
            if average is not None and average < minimum:
                raise ValueError(
                    f"GOPObservation average {label} must not be "
                    f"below minimum {label}"
                )

            if median is not None and median < minimum:
                raise ValueError(
                    f"GOPObservation median {label} must not be "
                    f"below minimum {label}"
                )

        if maximum is not None:
            if average is not None and average > maximum:
                raise ValueError(
                    f"GOPObservation average {label} must not exceed "
                    f"maximum {label}"
                )

            if median is not None and median > maximum:
                raise ValueError(
                    f"GOPObservation median {label} must not exceed "
                    f"maximum {label}"
                )


@dataclass(frozen=True, slots=True)
class VideoTrackObservation:
    """Observed video-track evidence."""

    availability: EvidenceAvailability

    codec: str | None = None
    profile: str | None = None
    level: str | None = None

    width: int | None = None
    height: int | None = None

    frame_rate: FrameRateObservation | None = None
    gop: GOPObservation | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "VideoTrackObservation.availability must be "
                "EvidenceAvailability"
            )

        for field_name in (
            "codec",
            "profile",
            "level",
        ):
            value = getattr(self, field_name)

            if value is None:
                continue

            if not isinstance(value, str):
                raise TypeError(
                    f"VideoTrackObservation.{field_name} must be "
                    "a str or None"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"VideoTrackObservation.{field_name} must not be "
                    "blank when present"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        for field_name in (
            "width",
            "height",
        ):
            value = getattr(self, field_name)

            if value is None:
                continue

            if (
                not isinstance(value, int)
                or isinstance(value, bool)
            ):
                raise TypeError(
                    f"VideoTrackObservation.{field_name} must be "
                    "an int or None"
                )

            if value <= 0:
                raise ValueError(
                    f"VideoTrackObservation.{field_name} must be "
                    "positive when present"
                )

        if (
            self.frame_rate is not None
            and not isinstance(
                self.frame_rate,
                FrameRateObservation,
            )
        ):
            raise TypeError(
                "VideoTrackObservation.frame_rate must be "
                "FrameRateObservation or None"
            )

        if (
            self.gop is not None
            and not isinstance(
                self.gop,
                GOPObservation,
            )
        ):
            raise TypeError(
                "VideoTrackObservation.gop must be "
                "GOPObservation or None"
            )


@dataclass(frozen=True, slots=True)
class AudioTrackObservation:
    """Observed audio-track evidence."""

    availability: EvidenceAvailability
    codec: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "AudioTrackObservation.availability must be "
                "EvidenceAvailability"
            )

        if self.codec is not None:
            normalized = self.codec.strip()

            if not normalized:
                raise ValueError(
                    "AudioTrackObservation.codec must not be "
                    "blank when present"
                )

            object.__setattr__(
                self,
                "codec",
                normalized,
            )


@dataclass(frozen=True, slots=True)
class InputMediaObservation:
    """Normalized evidence for one multimedia input observation."""

    node_id: NodeId
    instance_id: NodeInstanceId
    service_id: str
    observed_at: datetime

    path_name: str | None = None
    container: ContainerObservation | None = None
    video: VideoTrackObservation | None = None
    audio: AudioTrackObservation | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, NodeId):
            raise TypeError(
                "InputMediaObservation.node_id must be a NodeId"
            )

        if not isinstance(
            self.instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "InputMediaObservation.instance_id must be "
                "a NodeInstanceId"
            )

        if not isinstance(self.service_id, str):
            raise TypeError(
                "InputMediaObservation.service_id must be a str"
            )

        service_id = self.service_id.strip()

        if not service_id:
            raise ValueError(
                "InputMediaObservation.service_id must not be blank"
            )

        object.__setattr__(
            self,
            "service_id",
            service_id,
        )

        if self.path_name is not None:
            if not isinstance(self.path_name, str):
                raise TypeError(
                    "InputMediaObservation.path_name must be "
                    "a str or None"
                )

            path_name = self.path_name.strip()

            if not path_name:
                raise ValueError(
                    "InputMediaObservation.path_name must not "
                    "be blank when present"
                )

            object.__setattr__(
                self,
                "path_name",
                path_name,
            )

        self._validate_observed_at()

        self._validate_optional_type(
            self.container,
            ContainerObservation,
            "container",
        )
        self._validate_optional_type(
            self.video,
            VideoTrackObservation,
            "video",
        )
        self._validate_optional_type(
            self.audio,
            AudioTrackObservation,
            "audio",
        )

    def _validate_observed_at(self) -> None:
        if not isinstance(self.observed_at, datetime):
            raise TypeError(
                "InputMediaObservation.observed_at must be a datetime"
            )

        if self.observed_at.tzinfo is None:
            raise ValueError(
                "InputMediaObservation.observed_at must be "
                "timezone-aware and UTC"
            )

        offset = self.observed_at.utcoffset()

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "InputMediaObservation.observed_at must be "
                "expressed in UTC"
            )

    @staticmethod
    def _validate_optional_type(
        value: object | None,
        expected_type: type,
        field_name: str,
    ) -> None:
        if value is not None and not isinstance(
            value,
            expected_type,
        ):
            raise TypeError(
                f"InputMediaObservation.{field_name} must be "
                f"{expected_type.__name__} or None"
            )
