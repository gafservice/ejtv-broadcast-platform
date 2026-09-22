"""Media evaluation domain contract.

ENG-013C — Contract 3

This module represents deterministic comparison results between
expected media and observed media evidence.

It intentionally does not:

- observe media;
- assign Health or severity;
- stabilize temporal state;
- emit events or alarms;
- persist runtime state;
- configure expected profiles.

A media evaluation is evidence about expectation conformance, not an
operational Health decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.domain.streaming.expected_media_profile import (
    MediaPresenceExpectation,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)


class MediaComparisonStatus(str, Enum):
    """Outcome of one deterministic media comparison."""

    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_EVALUATED = "not_evaluated"

    def __str__(self) -> str:
        return self.value


def evaluate_presence(
    *,
    presence: MediaPresenceExpectation,
    availability: EvidenceAvailability | None,
) -> MediaComparisonStatus:
    """Evaluate declarative presence against observed availability.

    Missing component observation, insufficient evidence and
    not-applicable evidence do not prove either conformance or
    non-conformance, so they remain NOT_EVALUATED.
    """

    if not isinstance(
        presence,
        MediaPresenceExpectation,
    ):
        raise TypeError(
            "presence must be a MediaPresenceExpectation"
        )

    if (
        availability is not None
        and not isinstance(
            availability,
            EvidenceAvailability,
        )
    ):
        raise TypeError(
            "availability must be EvidenceAvailability or None"
        )

    if availability is None:
        return MediaComparisonStatus.NOT_EVALUATED

    if availability in {
        EvidenceAvailability.INSUFFICIENT,
        EvidenceAvailability.NOT_APPLICABLE,
    }:
        return MediaComparisonStatus.NOT_EVALUATED

    if presence is MediaPresenceExpectation.REQUIRED:
        if availability is EvidenceAvailability.AVAILABLE:
            return MediaComparisonStatus.MATCH

        return MediaComparisonStatus.MISMATCH

    if presence is MediaPresenceExpectation.OPTIONAL:
        return MediaComparisonStatus.MATCH

    if presence is MediaPresenceExpectation.FORBIDDEN:
        if availability is EvidenceAvailability.AVAILABLE:
            return MediaComparisonStatus.MISMATCH

        return MediaComparisonStatus.MATCH

    raise RuntimeError(
        "unreachable MediaPresenceExpectation state"
    )


@dataclass(frozen=True, slots=True)
class MediaFieldEvaluation:
    """Comparison evidence for one descriptive media field."""

    field_name: str
    expected: Any
    observed: Any
    status: MediaComparisonStatus

    def __post_init__(self) -> None:
        if not isinstance(self.field_name, str):
            raise TypeError(
                "MediaFieldEvaluation.field_name must be a str"
            )

        field_name = self.field_name.strip()

        if not field_name:
            raise ValueError(
                "MediaFieldEvaluation.field_name must not be blank"
            )

        object.__setattr__(
            self,
            "field_name",
            field_name,
        )

        if not isinstance(
            self.status,
            MediaComparisonStatus,
        ):
            raise TypeError(
                "MediaFieldEvaluation.status must be "
                "a MediaComparisonStatus"
            )


@dataclass(frozen=True, slots=True)
class MediaComponentEvaluation:
    """Evaluation evidence for one media component."""

    component: str
    presence_expectation: MediaPresenceExpectation
    evidence_availability: EvidenceAvailability | None
    presence_status: MediaComparisonStatus
    comparisons: tuple[MediaFieldEvaluation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.component, str):
            raise TypeError(
                "MediaComponentEvaluation.component must be a str"
            )

        component = self.component.strip()

        if not component:
            raise ValueError(
                "MediaComponentEvaluation.component must not be blank"
            )

        object.__setattr__(
            self,
            "component",
            component,
        )

        if not isinstance(
            self.presence_expectation,
            MediaPresenceExpectation,
        ):
            raise TypeError(
                "MediaComponentEvaluation.presence_expectation "
                "must be a MediaPresenceExpectation"
            )

        if (
            self.evidence_availability is not None
            and not isinstance(
                self.evidence_availability,
                EvidenceAvailability,
            )
        ):
            raise TypeError(
                "MediaComponentEvaluation.evidence_availability "
                "must be EvidenceAvailability or None"
            )

        if not isinstance(
            self.presence_status,
            MediaComparisonStatus,
        ):
            raise TypeError(
                "MediaComponentEvaluation.presence_status must be "
                "a MediaComparisonStatus"
            )

        if not isinstance(self.comparisons, tuple):
            raise TypeError(
                "MediaComponentEvaluation.comparisons must be a tuple"
            )

        for comparison in self.comparisons:
            if not isinstance(
                comparison,
                MediaFieldEvaluation,
            ):
                raise TypeError(
                    "MediaComponentEvaluation.comparisons must "
                    "contain MediaFieldEvaluation values"
                )


@dataclass(frozen=True, slots=True)
class MediaEvaluation:
    """Stateless media-evaluation result for one expected profile."""

    profile_id: str
    service_id: str
    path_name: str | None = None

    container: MediaComponentEvaluation | None = None
    video: MediaComponentEvaluation | None = None
    audio: MediaComponentEvaluation | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "profile_id",
            "service_id",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str):
                raise TypeError(
                    f"MediaEvaluation.{field_name} must be a str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"MediaEvaluation.{field_name} must not be blank"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if self.path_name is not None:
            if not isinstance(self.path_name, str):
                raise TypeError(
                    "MediaEvaluation.path_name must be str or None"
                )

            path_name = self.path_name.strip()

            if not path_name:
                raise ValueError(
                    "MediaEvaluation.path_name must not be blank "
                    "when present"
                )

            object.__setattr__(
                self,
                "path_name",
                path_name,
            )

        for field_name in (
            "container",
            "video",
            "audio",
        ):
            value = getattr(self, field_name)

            if (
                value is not None
                and not isinstance(
                    value,
                    MediaComponentEvaluation,
                )
            ):
                raise TypeError(
                    f"MediaEvaluation.{field_name} must be "
                    "MediaComponentEvaluation or None"
                )


class MediaEvaluator:
    """Compare declared media expectations with observed evidence.

    This evaluator is intentionally stateless.

    It produces descriptive comparison evidence only. It does not assign
    Health, severity, alarms, events, stabilization state, or persistence.
    """

    def evaluate(
        self,
        *,
        profile: object,
        observation: object,
    ) -> MediaEvaluation:
        from app.domain.streaming.expected_media_profile import (
            ExpectedMediaProfile,
        )
        from app.domain.streaming.media_observation import (
            InputMediaObservation,
        )

        if not isinstance(profile, ExpectedMediaProfile):
            raise TypeError(
                "profile must be an ExpectedMediaProfile"
            )

        if not isinstance(observation, InputMediaObservation):
            raise TypeError(
                "observation must be an InputMediaObservation"
            )

        if profile.service_id != observation.service_id:
            raise ValueError(
                "observation service_id does not match "
                "expected media profile service_id"
            )

        if (
            profile.path_name is not None
            and profile.path_name != observation.path_name
        ):
            raise ValueError(
                "observation path_name does not match "
                "expected media profile path_name"
            )

        return MediaEvaluation(
            profile_id=profile.profile_id,
            service_id=profile.service_id,
            path_name=profile.path_name,
            container=self._evaluate_component(
                component="container",
                expected=profile.container,
                observed=observation.container,
            ),
            video=self._evaluate_component(
                component="video",
                expected=profile.video,
                observed=observation.video,
            ),
            audio=self._evaluate_component(
                component="audio",
                expected=profile.audio,
                observed=observation.audio,
            ),
        )

    def _evaluate_component(
        self,
        *,
        component: str,
        expected: object | None,
        observed: object | None,
    ) -> MediaComponentEvaluation | None:
        if expected is None:
            return None

        availability = (
            None
            if observed is None
            else observed.availability
        )

        presence_status = evaluate_presence(
            presence=expected.presence,
            availability=availability,
        )

        comparisons: tuple[MediaFieldEvaluation, ...]

        if component == "container":
            comparisons = self._evaluate_container(
                expected=expected,
                observed=observed,
            )
        elif component == "video":
            comparisons = self._evaluate_video(
                expected=expected,
                observed=observed,
            )
        elif component == "audio":
            comparisons = self._evaluate_audio(
                expected=expected,
                observed=observed,
            )
        else:
            raise RuntimeError(
                f"unsupported media component: {component}"
            )

        return MediaComponentEvaluation(
            component=component,
            presence_expectation=expected.presence,
            evidence_availability=availability,
            presence_status=presence_status,
            comparisons=comparisons,
        )

    @staticmethod
    def _compare(
        *,
        field_name: str,
        expected: object,
        observed: object,
    ) -> MediaFieldEvaluation:
        if observed is None:
            status = MediaComparisonStatus.NOT_EVALUATED
        elif observed == expected:
            status = MediaComparisonStatus.MATCH
        else:
            status = MediaComparisonStatus.MISMATCH

        return MediaFieldEvaluation(
            field_name=field_name,
            expected=expected,
            observed=observed,
            status=status,
        )

    def _evaluate_container(
        self,
        *,
        expected: object,
        observed: object | None,
    ) -> tuple[MediaFieldEvaluation, ...]:
        comparisons: list[MediaFieldEvaluation] = []

        if expected.container_type is not None:
            comparisons.append(
                self._compare(
                    field_name="container_type",
                    expected=expected.container_type,
                    observed=(
                        None
                        if observed is None
                        else observed.container_type
                    ),
                )
            )

        return tuple(comparisons)

    def _evaluate_video(
        self,
        *,
        expected: object,
        observed: object | None,
    ) -> tuple[MediaFieldEvaluation, ...]:
        comparisons: list[MediaFieldEvaluation] = []

        for field_name in (
            "codec",
            "profile",
            "level",
            "width",
            "height",
        ):
            expected_value = getattr(
                expected,
                field_name,
            )

            if expected_value is None:
                continue

            observed_value = (
                None
                if observed is None
                else getattr(
                    observed,
                    field_name,
                )
            )

            comparisons.append(
                self._compare(
                    field_name=field_name,
                    expected=expected_value,
                    observed=observed_value,
                )
            )

        if (
            expected.frame_rate_numerator is not None
            and expected.frame_rate_denominator is not None
        ):
            expected_frame_rate = (
                expected.frame_rate_numerator,
                expected.frame_rate_denominator,
            )

            if (
                observed is None
                or observed.frame_rate is None
            ):
                observed_frame_rate = None
            else:
                observed_frame_rate = (
                    observed.frame_rate.numerator,
                    observed.frame_rate.denominator,
                )

            comparisons.append(
                self._compare(
                    field_name="frame_rate",
                    expected=expected_frame_rate,
                    observed=observed_frame_rate,
                )
            )

        if expected.gop_interval_seconds is not None:
            comparisons.append(
                MediaFieldEvaluation(
                    field_name="gop_interval_seconds",
                    expected=expected.gop_interval_seconds,
                    observed=None,
                    status=(
                        MediaComparisonStatus.NOT_EVALUATED
                    ),
                )
            )

        return tuple(comparisons)

    def _evaluate_audio(
        self,
        *,
        expected: object,
        observed: object | None,
    ) -> tuple[MediaFieldEvaluation, ...]:
        comparisons: list[MediaFieldEvaluation] = []

        for field_name in (
            "codec",
            "profile",
            "sample_rate",
            "channels",
            "channel_layout",
        ):
            expected_value = getattr(
                expected,
                field_name,
            )

            if expected_value is None:
                continue

            observed_value = (
                None
                if observed is None
                else getattr(
                    observed,
                    field_name,
                )
            )

            comparisons.append(
                self._compare(
                    field_name=field_name,
                    expected=expected_value,
                    observed=observed_value,
                )
            )

        return tuple(comparisons)
