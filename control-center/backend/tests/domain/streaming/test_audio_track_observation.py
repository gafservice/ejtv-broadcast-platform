"""Tests for ENG-013C audio-track observation evidence."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.domain.streaming.media_observation import (
    AudioTrackObservation,
    EvidenceAvailability,
)


def test_audio_track_preserves_descriptive_evidence() -> None:
    observation = AudioTrackObservation(
        availability=EvidenceAvailability.AVAILABLE,
        codec=" AAC ",
        profile=" LC ",
        sample_rate=48000,
        channels=2,
        channel_layout=" stereo ",
    )

    assert observation.availability is EvidenceAvailability.AVAILABLE
    assert observation.codec == "AAC"
    assert observation.profile == "LC"
    assert observation.sample_rate == 48000
    assert observation.channels == 2
    assert observation.channel_layout == "stereo"

    assert not hasattr(observation, "health")
    assert not hasattr(observation, "status")


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("codec", ""),
        ("codec", "   "),
        ("profile", ""),
        ("profile", "   "),
        ("channel_layout", ""),
        ("channel_layout", "   "),
    ],
)
def test_audio_track_rejects_blank_descriptive_strings(
    field_name: str,
    value: str,
) -> None:
    kwargs = {
        "availability": EvidenceAvailability.AVAILABLE,
        field_name: value,
    }

    with pytest.raises(ValueError):
        AudioTrackObservation(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("sample_rate", 0),
        ("sample_rate", -1),
        ("channels", 0),
        ("channels", -1),
    ],
)
def test_audio_track_rejects_non_positive_integer_evidence(
    field_name: str,
    value: int,
) -> None:
    kwargs = {
        "availability": EvidenceAvailability.AVAILABLE,
        field_name: value,
    }

    with pytest.raises(ValueError):
        AudioTrackObservation(**kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("sample_rate", 48000.0),
        ("sample_rate", True),
        ("sample_rate", "48000"),
        ("channels", 2.0),
        ("channels", True),
        ("channels", "2"),
    ],
)
def test_audio_track_integer_evidence_requires_integers(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        "availability": EvidenceAvailability.AVAILABLE,
        field_name: value,
    }

    with pytest.raises(TypeError):
        AudioTrackObservation(**kwargs)


def test_audio_track_allows_partial_descriptive_evidence() -> None:
    observation = AudioTrackObservation(
        availability=EvidenceAvailability.AVAILABLE,
        codec="AAC",
        profile=None,
        sample_rate=None,
        channels=None,
        channel_layout=None,
    )

    assert observation.codec == "AAC"
    assert observation.profile is None
    assert observation.sample_rate is None
    assert observation.channels is None
    assert observation.channel_layout is None


@pytest.mark.parametrize(
    "availability",
    list(EvidenceAvailability),
)
def test_audio_track_supports_every_evidence_availability(
    availability: EvidenceAvailability,
) -> None:
    observation = AudioTrackObservation(
        availability=availability,
        codec=None,
        profile=None,
        sample_rate=None,
        channels=None,
        channel_layout=None,
    )

    assert observation.availability is availability


def test_audio_track_rejects_invalid_availability_type() -> None:
    with pytest.raises(TypeError):
        AudioTrackObservation(
            availability="AVAILABLE",
        )


def test_audio_track_is_immutable() -> None:
    observation = AudioTrackObservation(
        availability=EvidenceAvailability.AVAILABLE,
        codec="AAC",
        profile="LC",
        sample_rate=48000,
        channels=2,
        channel_layout="stereo",
    )

    with pytest.raises(FrozenInstanceError):
        observation.channels = 1
