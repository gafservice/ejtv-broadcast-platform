from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.streaming.media_observation import (
    AudioTrackObservation,
    ContainerObservation,
    EvidenceAvailability,
    InputMediaObservation,
    VideoTrackObservation,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId


UTC_NOW = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)


def make_node_id() -> NodeId:
    return NodeId(
        id="ejtv-01",
        name="ejtv-01",
        display_name="EJTV 01",
        created_at=UTC_NOW,
    )


def make_observation(**overrides) -> InputMediaObservation:
    values = {
        "node_id": make_node_id(),
        "instance_id": NodeInstanceId("ejtv-01-runtime"),
        "service_id": "impact",
        "path_name": "impact",
        "observed_at": UTC_NOW,
        "container": None,
        "video": None,
        "audio": None,
    }
    values.update(overrides)
    return InputMediaObservation(**values)


def test_evidence_availability_is_independent_domain_state() -> None:
    assert EvidenceAvailability.AVAILABLE.value == "available"
    assert EvidenceAvailability.UNAVAILABLE.value == "unavailable"
    assert EvidenceAvailability.INSUFFICIENT.value == "insufficient"
    assert EvidenceAvailability.NOT_APPLICABLE.value == "not_applicable"


def test_input_media_observation_preserves_nodal_identity() -> None:
    observation = make_observation()

    assert observation.node_id.id == "ejtv-01"
    assert observation.instance_id == NodeInstanceId("ejtv-01-runtime")
    assert observation.service_id == "impact"
    assert observation.path_name == "impact"
    assert observation.observed_at == UTC_NOW


def test_input_media_observation_normalizes_service_and_path() -> None:
    observation = make_observation(
        service_id="  impact  ",
        path_name="  impact  ",
    )

    assert observation.service_id == "impact"
    assert observation.path_name == "impact"


@pytest.mark.parametrize("service_id", ["", " ", "\t"])
def test_input_media_observation_rejects_blank_service_id(
    service_id: str,
) -> None:
    with pytest.raises(ValueError):
        make_observation(service_id=service_id)


def test_input_media_observation_allows_absent_path() -> None:
    observation = make_observation(path_name=None)

    assert observation.path_name is None


@pytest.mark.parametrize("path_name", ["", " ", "\t"])
def test_input_media_observation_rejects_blank_path_when_present(
    path_name: str,
) -> None:
    with pytest.raises(ValueError):
        make_observation(path_name=path_name)


def test_input_media_observation_rejects_naive_observed_at() -> None:
    with pytest.raises(ValueError):
        make_observation(
            observed_at=datetime(2026, 9, 18, 20, 0),
        )


def test_input_media_observation_rejects_non_utc_observed_at() -> None:
    non_utc = timezone(timedelta(hours=-6))

    with pytest.raises(ValueError):
        make_observation(
            observed_at=datetime(
                2026,
                9,
                18,
                14,
                0,
                tzinfo=non_utc,
            ),
        )


def test_input_media_observation_rejects_invalid_node_id_type() -> None:
    with pytest.raises(TypeError):
        make_observation(node_id="ejtv-01")


def test_input_media_observation_rejects_invalid_instance_id_type() -> None:
    with pytest.raises(TypeError):
        make_observation(instance_id="ejtv-01-runtime")


def test_container_observation_carries_availability_without_health() -> None:
    container = ContainerObservation(
        availability=EvidenceAvailability.AVAILABLE,
        container_type="mpegts",
    )

    assert container.availability is EvidenceAvailability.AVAILABLE
    assert container.container_type == "mpegts"
    assert not hasattr(container, "health")
    assert not hasattr(container, "status")


def test_video_and_audio_observations_are_independent() -> None:
    video = VideoTrackObservation(
        availability=EvidenceAvailability.AVAILABLE,
        codec="h264",
    )
    audio = AudioTrackObservation(
        availability=EvidenceAvailability.UNAVAILABLE,
        codec=None,
    )

    observation = make_observation(
        video=video,
        audio=audio,
    )

    assert observation.video is video
    assert observation.audio is audio
    assert observation.video.availability is EvidenceAvailability.AVAILABLE
    assert observation.audio.availability is EvidenceAvailability.UNAVAILABLE


def test_missing_track_observations_do_not_create_health_state() -> None:
    observation = make_observation(
        video=None,
        audio=None,
    )

    assert observation.video is None
    assert observation.audio is None
    assert not hasattr(observation, "health")
    assert not hasattr(observation, "status")


def test_observation_objects_are_immutable() -> None:
    observation = make_observation()

    with pytest.raises(FrozenInstanceError):
        observation.service_id = "ejtv"
