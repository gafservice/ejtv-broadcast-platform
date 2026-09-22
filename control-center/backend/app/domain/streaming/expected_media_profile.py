"""Expected media profile domain contract.

ENG-013C — Contract 2

This module describes what media is expected for one logical service.

It is intentionally declarative:

- it does not observe media;
- it does not evaluate observations;
- it does not assign Health;
- it does not stabilize state;
- it does not emit events or alarms;
- it does not persist runtime state.

Runtime node identity belongs to observation, not to the reusable
expected-media profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MediaPresenceExpectation(str, Enum):
    """Expected presence of one media component."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    FORBIDDEN = "forbidden"

    def __str__(self) -> str:
        return self.value


def _normalize_optional_text(
    value: str | None,
    *,
    field_name: str,
) -> str | None:
    """Normalize optional descriptive text."""

    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a str or None"
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} must not be blank"
        )

    return normalized


def _validate_presence(
    value: MediaPresenceExpectation,
) -> None:
    """Require explicit presence semantics."""

    if not isinstance(
        value,
        MediaPresenceExpectation,
    ):
        raise TypeError(
            "presence must be a MediaPresenceExpectation"
        )


def _validate_optional_positive_int(
    value: int | None,
    *,
    field_name: str,
) -> None:
    """Validate an optional strictly positive integer."""

    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{field_name} must be an int or None"
        )

    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than zero"
        )


@dataclass(frozen=True, slots=True)
class ExpectedContainerProfile:
    """Declarative container expectation."""

    presence: MediaPresenceExpectation
    container_type: str | None = None

    def __post_init__(self) -> None:
        _validate_presence(self.presence)

        object.__setattr__(
            self,
            "container_type",
            _normalize_optional_text(
                self.container_type,
                field_name="container_type",
            ),
        )


@dataclass(frozen=True, slots=True)
class ExpectedVideoProfile:
    """Declarative video-track expectation."""

    presence: MediaPresenceExpectation

    codec: str | None = None
    profile: str | None = None
    level: str | None = None

    width: int | None = None
    height: int | None = None

    frame_rate_numerator: int | None = None
    frame_rate_denominator: int | None = None

    gop_interval_seconds: float | None = None

    def __post_init__(self) -> None:
        _validate_presence(self.presence)

        for field_name in (
            "codec",
            "profile",
            "level",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        _validate_optional_positive_int(
            self.width,
            field_name="width",
        )
        _validate_optional_positive_int(
            self.height,
            field_name="height",
        )

        numerator = self.frame_rate_numerator
        denominator = self.frame_rate_denominator

        if (numerator is None) != (denominator is None):
            raise ValueError(
                "frame rate numerator and denominator "
                "must be configured together"
            )

        _validate_optional_positive_int(
            numerator,
            field_name="frame_rate_numerator",
        )
        _validate_optional_positive_int(
            denominator,
            field_name="frame_rate_denominator",
        )

        if self.gop_interval_seconds is not None:
            if (
                isinstance(
                    self.gop_interval_seconds,
                    bool,
                )
                or not isinstance(
                    self.gop_interval_seconds,
                    (int, float),
                )
            ):
                raise TypeError(
                    "gop_interval_seconds must be "
                    "numeric or None"
                )

            if self.gop_interval_seconds <= 0:
                raise ValueError(
                    "gop_interval_seconds must be "
                    "greater than zero"
                )


@dataclass(frozen=True, slots=True)
class ExpectedAudioProfile:
    """Declarative audio-track expectation."""

    presence: MediaPresenceExpectation

    codec: str | None = None
    profile: str | None = None
    sample_rate: int | None = None
    channels: int | None = None
    channel_layout: str | None = None

    def __post_init__(self) -> None:
        _validate_presence(self.presence)

        for field_name in (
            "codec",
            "profile",
            "channel_layout",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_text(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

        _validate_optional_positive_int(
            self.sample_rate,
            field_name="sample_rate",
        )
        _validate_optional_positive_int(
            self.channels,
            field_name="channels",
        )


@dataclass(frozen=True, slots=True)
class ExpectedMediaProfile:
    """Reusable expected-media definition for one logical service."""

    profile_id: str
    service_id: str
    path_name: str | None = None

    container: ExpectedContainerProfile | None = None
    video: ExpectedVideoProfile | None = None
    audio: ExpectedAudioProfile | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.profile_id, str):
            raise TypeError(
                "profile_id must be a str"
            )

        if not isinstance(self.service_id, str):
            raise TypeError(
                "service_id must be a str"
            )

        profile_id = self.profile_id.strip()
        service_id = self.service_id.strip()

        if not profile_id:
            raise ValueError(
                "profile_id must not be blank"
            )

        if not service_id:
            raise ValueError(
                "service_id must not be blank"
            )

        object.__setattr__(
            self,
            "profile_id",
            profile_id,
        )
        object.__setattr__(
            self,
            "service_id",
            service_id,
        )

        object.__setattr__(
            self,
            "path_name",
            _normalize_optional_text(
                self.path_name,
                field_name="path_name",
            ),
        )

        component_types = (
            (
                "container",
                self.container,
                ExpectedContainerProfile,
            ),
            (
                "video",
                self.video,
                ExpectedVideoProfile,
            ),
            (
                "audio",
                self.audio,
                ExpectedAudioProfile,
            ),
        )

        for (
            field_name,
            value,
            expected_type,
        ) in component_types:
            if (
                value is not None
                and not isinstance(
                    value,
                    expected_type,
                )
            ):
                raise TypeError(
                    f"{field_name} must be "
                    f"{expected_type.__name__} or None"
                )
