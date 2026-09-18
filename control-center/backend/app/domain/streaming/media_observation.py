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


@dataclass(frozen=True, slots=True)
class ContainerObservation:
    """Generic container-level evidence."""

    availability: EvidenceAvailability
    container_type: str | None = None

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


@dataclass(frozen=True, slots=True)
class VideoTrackObservation:
    """Observed video-track evidence."""

    availability: EvidenceAvailability
    codec: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.availability,
            EvidenceAvailability,
        ):
            raise TypeError(
                "VideoTrackObservation.availability must be "
                "EvidenceAvailability"
            )

        if self.codec is not None:
            normalized = self.codec.strip()

            if not normalized:
                raise ValueError(
                    "VideoTrackObservation.codec must not be "
                    "blank when present"
                )

            object.__setattr__(
                self,
                "codec",
                normalized,
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
