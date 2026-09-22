"""Tests for NodeMediaProfileLoader."""

from pathlib import Path

import pytest

from app.domain.streaming.expected_media_profile import (
    MediaPresenceExpectation,
)
from app.noc.infrastructure.node_media_profile_loader import (
    NodeMediaProfileLoader,
)


def valid_payload() -> dict:
    return {
        "node": "ejtv-01",
        "network_interfaces": [],
        "session_policies": {},
        "media_profiles": [
            {
                "profile_id": "impact-main",
                "service_id": "impact",
                "path_name": "impact",
                "video": {
                    "presence": "required",
                    "codec": "h264",
                    "profile": "Main",
                    "level": "40",
                    "width": 1920,
                    "height": 1080,
                    "frame_rate": {
                        "numerator": 30,
                        "denominator": 1,
                    },
                },
                "audio": {
                    "presence": "required",
                    "codec": "aac",
                    "profile": "LC",
                    "sample_rate": 48000,
                    "channels": 2,
                    "channel_layout": "stereo",
                },
            }
        ],
    }


def test_from_mapping_builds_expected_media_profile() -> None:
    profiles = NodeMediaProfileLoader().from_mapping(
        valid_payload()
    )

    assert isinstance(profiles, tuple)
    assert len(profiles) == 1

    profile = profiles[0]

    assert profile.profile_id == "impact-main"
    assert profile.service_id == "impact"
    assert profile.path_name == "impact"

    assert profile.container is None

    assert profile.video is not None
    assert (
        profile.video.presence
        is MediaPresenceExpectation.REQUIRED
    )
    assert profile.video.codec == "h264"
    assert profile.video.profile == "Main"
    assert profile.video.level == "40"
    assert profile.video.width == 1920
    assert profile.video.height == 1080
    assert (
        profile.video.frame_rate_numerator,
        profile.video.frame_rate_denominator,
    ) == (30, 1)
    assert profile.video.gop_interval_seconds is None

    assert profile.audio is not None
    assert (
        profile.audio.presence
        is MediaPresenceExpectation.REQUIRED
    )
    assert profile.audio.codec == "aac"
    assert profile.audio.profile == "LC"
    assert profile.audio.sample_rate == 48000
    assert profile.audio.channels == 2
    assert profile.audio.channel_layout == "stereo"


def test_from_mapping_allows_empty_media_profiles() -> None:
    profiles = NodeMediaProfileLoader().from_mapping(
        {"media_profiles": []}
    )

    assert profiles == ()


def test_from_mapping_requires_media_profiles_section() -> None:
    with pytest.raises(
        ValueError,
        match="media_profiles",
    ):
        NodeMediaProfileLoader().from_mapping(
            {"node": "ejtv-01"}
        )


def test_from_mapping_requires_media_profiles_list() -> None:
    with pytest.raises(TypeError):
        NodeMediaProfileLoader().from_mapping(
            {"media_profiles": {}}
        )


def test_from_mapping_rejects_non_mapping_profile() -> None:
    with pytest.raises(TypeError):
        NodeMediaProfileLoader().from_mapping(
            {"media_profiles": ["impact-main"]}
        )


def test_presence_is_translated_to_domain_enum() -> None:
    payload = valid_payload()

    payload["media_profiles"][0]["video"][
        "presence"
    ] = "optional"

    profiles = NodeMediaProfileLoader().from_mapping(
        payload
    )

    assert (
        profiles[0].video.presence
        is MediaPresenceExpectation.OPTIONAL
    )


def test_invalid_presence_is_rejected() -> None:
    payload = valid_payload()

    payload["media_profiles"][0]["video"][
        "presence"
    ] = "sometimes"

    with pytest.raises(ValueError):
        NodeMediaProfileLoader().from_mapping(
            payload
        )


def test_frame_rate_requires_mapping() -> None:
    payload = valid_payload()

    payload["media_profiles"][0]["video"][
        "frame_rate"
    ] = "30/1"

    with pytest.raises(TypeError):
        NodeMediaProfileLoader().from_mapping(
            payload
        )


def test_load_reads_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "node.yaml"

    path.write_text(
        """
node: ejtv-01

media_profiles:
  - profile_id: impact-main
    service_id: impact
    path_name: impact

    video:
      presence: required
      codec: h264
      width: 1920
      height: 1080
      frame_rate:
        numerator: 30
        denominator: 1

    audio:
      presence: required
      codec: aac
      sample_rate: 48000
      channels: 2
      channel_layout: stereo
""",
        encoding="utf-8",
    )

    profiles = NodeMediaProfileLoader().load(path)

    assert len(profiles) == 1
    assert profiles[0].profile_id == "impact-main"
    assert profiles[0].video is not None
    assert profiles[0].video.width == 1920
    assert profiles[0].audio is not None
    assert profiles[0].audio.sample_rate == 48000


def test_missing_file_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        NodeMediaProfileLoader().load(
            tmp_path / "missing.yaml"
        )


def test_duplicate_profile_id_is_rejected() -> None:
    payload = valid_payload()

    duplicate = dict(
        payload["media_profiles"][0]
    )
    duplicate["service_id"] = "ejtv"
    duplicate["path_name"] = "ejtv"

    payload["media_profiles"].append(
        duplicate
    )

    with pytest.raises(
        ValueError,
        match="profile_id",
    ):
        NodeMediaProfileLoader().from_mapping(
            payload
        )


def test_duplicate_service_path_identity_is_rejected() -> None:
    payload = valid_payload()

    duplicate = dict(
        payload["media_profiles"][0]
    )
    duplicate["profile_id"] = "impact-backup"

    payload["media_profiles"].append(
        duplicate
    )

    with pytest.raises(
        ValueError,
        match="service_id.*path_name|identity",
    ):
        NodeMediaProfileLoader().from_mapping(
            payload
        )


@pytest.mark.parametrize(
    "component",
    [
        "container",
        "video",
        "audio",
    ],
)
def test_component_must_be_mapping_when_present(
    component: str,
) -> None:
    payload = valid_payload()

    payload["media_profiles"][0][component] = (
        "invalid"
    )

    with pytest.raises(
        TypeError,
        match=component,
    ):
        NodeMediaProfileLoader().from_mapping(
            payload
        )


def test_frame_rate_requires_numerator_and_denominator() -> None:
    payload = valid_payload()

    payload["media_profiles"][0]["video"][
        "frame_rate"
    ] = {
        "numerator": 30,
    }

    with pytest.raises(
        ValueError,
        match="frame rate|frame_rate|numerator|denominator",
    ):
        NodeMediaProfileLoader().from_mapping(
            payload
        )


def test_multiple_distinct_profiles_are_allowed() -> None:
    payload = valid_payload()

    second = {
        "profile_id": "ejtv-main",
        "service_id": "ejtv",
        "path_name": "ejtv",
        "video": {
            "presence": "required",
            "codec": "h264",
        },
        "audio": {
            "presence": "required",
            "codec": "aac",
        },
    }

    payload["media_profiles"].append(
        second
    )

    profiles = NodeMediaProfileLoader().from_mapping(
        payload
    )

    assert len(profiles) == 2
    assert profiles[0].profile_id == "impact-main"
    assert profiles[1].profile_id == "ejtv-main"
