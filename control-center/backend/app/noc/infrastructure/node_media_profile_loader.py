"""Load expected media profiles from node configuration."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from app.domain.streaming.expected_media_profile import (
    ExpectedAudioProfile,
    ExpectedContainerProfile,
    ExpectedMediaProfile,
    ExpectedVideoProfile,
    MediaPresenceExpectation,
)


class NodeMediaProfileLoader:
    """Load ExpectedMediaProfile objects from node configuration."""

    def load(
        self,
        path: str | Path,
    ) -> tuple[ExpectedMediaProfile, ...]:
        config_path = Path(path)

        if not config_path.is_file():
            raise FileNotFoundError(config_path)

        payload = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )

        return self.from_mapping(payload)

    def from_mapping(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[ExpectedMediaProfile, ...]:
        if not isinstance(payload, Mapping):
            raise TypeError(
                "node configuration must be a mapping"
            )

        if "media_profiles" not in payload:
            raise ValueError(
                "node configuration must contain media_profiles"
            )

        raw_profiles = payload["media_profiles"]

        if not isinstance(raw_profiles, list):
            raise TypeError(
                "media_profiles must be a list"
            )

        profiles: list[ExpectedMediaProfile] = []
        profile_ids: set[str] = set()
        operational_identities: set[
            tuple[str, str | None]
        ] = set()

        for raw_profile in raw_profiles:
            if not isinstance(raw_profile, Mapping):
                raise TypeError(
                    "each media profile must be a mapping"
                )

            profile = self._build_profile(
                raw_profile
            )

            if profile.profile_id in profile_ids:
                raise ValueError(
                    "duplicate media profile_id: "
                    f"{profile.profile_id}"
                )

            operational_identity = (
                profile.service_id,
                profile.path_name,
            )

            if (
                operational_identity
                in operational_identities
            ):
                raise ValueError(
                    "duplicate media profile identity "
                    "(service_id, path_name): "
                    f"{operational_identity!r}"
                )

            profile_ids.add(
                profile.profile_id
            )
            operational_identities.add(
                operational_identity
            )
            profiles.append(profile)

        return tuple(profiles)

    def _build_profile(
        self,
        raw: Mapping[str, Any],
    ) -> ExpectedMediaProfile:
        return ExpectedMediaProfile(
            profile_id=raw["profile_id"],
            service_id=raw["service_id"],
            path_name=raw.get("path_name"),
            container=self._build_container(
                raw.get("container")
            ),
            video=self._build_video(
                raw.get("video")
            ),
            audio=self._build_audio(
                raw.get("audio")
            ),
        )

    def _build_container(
        self,
        raw: Any,
    ) -> ExpectedContainerProfile | None:
        if raw is None:
            return None

        mapping = self._require_mapping(
            raw,
            field_name="container",
        )

        return ExpectedContainerProfile(
            presence=self._presence(
                mapping["presence"]
            ),
            container_type=mapping.get(
                "container_type"
            ),
        )

    def _build_video(
        self,
        raw: Any,
    ) -> ExpectedVideoProfile | None:
        if raw is None:
            return None

        mapping = self._require_mapping(
            raw,
            field_name="video",
        )

        numerator = None
        denominator = None

        if "frame_rate" in mapping:
            frame_rate = self._require_mapping(
                mapping["frame_rate"],
                field_name="frame_rate",
            )

            numerator = frame_rate.get("numerator")
            denominator = frame_rate.get("denominator")

        return ExpectedVideoProfile(
            presence=self._presence(
                mapping["presence"]
            ),
            codec=mapping.get("codec"),
            profile=mapping.get("profile"),
            level=mapping.get("level"),
            width=mapping.get("width"),
            height=mapping.get("height"),
            frame_rate_numerator=numerator,
            frame_rate_denominator=denominator,
            gop_interval_seconds=mapping.get(
                "gop_interval_seconds"
            ),
        )

    def _build_audio(
        self,
        raw: Any,
    ) -> ExpectedAudioProfile | None:
        if raw is None:
            return None

        mapping = self._require_mapping(
            raw,
            field_name="audio",
        )

        return ExpectedAudioProfile(
            presence=self._presence(
                mapping["presence"]
            ),
            codec=mapping.get("codec"),
            profile=mapping.get("profile"),
            sample_rate=mapping.get("sample_rate"),
            channels=mapping.get("channels"),
            channel_layout=mapping.get(
                "channel_layout"
            ),
        )

    @staticmethod
    def _require_mapping(
        value: Any,
        *,
        field_name: str,
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise TypeError(
                f"{field_name} must be a mapping"
            )

        return value

    @staticmethod
    def _presence(
        value: Any,
    ) -> MediaPresenceExpectation:
        if not isinstance(value, str):
            raise TypeError(
                "presence must be a string"
            )

        try:
            return MediaPresenceExpectation(value)
        except ValueError as exc:
            raise ValueError(
                f"invalid media presence: {value!r}"
            ) from exc
