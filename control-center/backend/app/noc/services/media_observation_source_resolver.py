"""Resolve generic physical media observation sources."""

from __future__ import annotations

from urllib.parse import urlsplit


class MediaObservationSourceResolver:
    """Resolve an observable MediaMTX RTSP source from a path identity."""

    def __init__(
        self,
        *,
        rtsp_base_url: str,
    ) -> None:
        if not isinstance(rtsp_base_url, str):
            raise TypeError(
                "rtsp_base_url must be a string"
            )

        normalized_base_url = rtsp_base_url.strip()

        if not normalized_base_url:
            raise ValueError(
                "rtsp_base_url must not be empty"
            )

        parsed = urlsplit(normalized_base_url)

        if parsed.scheme.lower() != "rtsp":
            raise ValueError(
                "rtsp_base_url must use rtsp scheme"
            )

        if not parsed.netloc:
            raise ValueError(
                "rtsp_base_url must include an authority"
            )

        if parsed.path not in ("", "/"):
            raise ValueError(
                "rtsp_base_url must not include a path"
            )

        if parsed.query or parsed.fragment:
            raise ValueError(
                "rtsp_base_url must not include query or fragment"
            )

        self._rtsp_base_url = (
            normalized_base_url.rstrip("/")
        )

    def resolve(
        self,
        *,
        path_name: str,
    ) -> str:
        """Return the observable RTSP source for one generic path."""

        if not isinstance(path_name, str):
            raise TypeError(
                "path_name must be a string"
            )

        normalized_path = path_name.strip()

        if not normalized_path:
            raise ValueError(
                "path_name must not be empty"
            )

        if normalized_path.startswith("/"):
            raise ValueError(
                "path_name must not start with '/'"
            )

        return (
            f"{self._rtsp_base_url}/"
            f"{normalized_path}"
        )
