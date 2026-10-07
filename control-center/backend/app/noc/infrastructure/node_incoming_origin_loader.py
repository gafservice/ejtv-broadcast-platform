"""Load expected incoming-origin identities from node configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml


class NodeIncomingOriginLoader:
    """Load expected incoming remote addresses keyed by media path."""

    def load(
        self,
        path: Path,
    ) -> dict[str, str]:
        if not isinstance(path, Path):
            raise TypeError("path must be a pathlib.Path")

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            payload = yaml.safe_load(handle)

        if payload is None:
            payload = {}

        return self.from_mapping(payload)

    def from_mapping(
        self,
        data: Mapping[str, Any],
    ) -> dict[str, str]:
        if not isinstance(data, Mapping):
            raise TypeError(
                "node configuration must be a mapping"
            )

        raw_origins = data.get(
            "incoming_origins",
            [],
        )

        if not isinstance(raw_origins, list):
            raise TypeError(
                "incoming_origins must be a list"
            )

        origins: dict[str, str] = {}

        for raw_origin in raw_origins:
            if not isinstance(raw_origin, Mapping):
                raise TypeError(
                    "each incoming origin must be a mapping"
                )

            if "path_name" not in raw_origin:
                raise ValueError(
                    "incoming origin must contain path_name"
                )

            path_name = raw_origin["path_name"]

            if not isinstance(path_name, str):
                raise TypeError(
                    "path_name must be a string"
                )

            path_name = path_name.strip()

            if not path_name:
                raise ValueError(
                    "path_name must not be blank"
                )

            if "expected_remote_address" not in raw_origin:
                raise ValueError(
                    "incoming origin must contain "
                    "expected_remote_address"
                )

            expected_remote_address = raw_origin[
                "expected_remote_address"
            ]

            if not isinstance(
                expected_remote_address,
                str,
            ):
                raise TypeError(
                    "expected_remote_address must be a string"
                )

            expected_remote_address = (
                expected_remote_address.strip()
            )

            if not expected_remote_address:
                raise ValueError(
                    "expected_remote_address must not be blank"
                )

            if path_name in origins:
                raise ValueError(
                    "duplicate incoming origin path_name "
                    f"{path_name!r}"
                )

            origins[path_name] = expected_remote_address

        return origins
