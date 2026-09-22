"""Contract tests for generic physical media observation source resolution."""

import pytest

from app.noc.services.media_observation_source_resolver import (
    MediaObservationSourceResolver,
)


def test_resolves_path_against_configured_rtsp_base_url() -> None:
    resolver = MediaObservationSourceResolver(
        rtsp_base_url="rtsp://127.0.0.1:8554",
    )

    assert (
        resolver.resolve(path_name="sat-primary")
        == "rtsp://127.0.0.1:8554/sat-primary"
    )


def test_resolution_does_not_require_service_identity() -> None:
    resolver = MediaObservationSourceResolver(
        rtsp_base_url="rtsp://media-node.internal:8554",
    )

    assert (
        resolver.resolve(path_name="feed-a")
        == "rtsp://media-node.internal:8554/feed-a"
    )


def test_trailing_base_slash_does_not_duplicate_separator() -> None:
    resolver = MediaObservationSourceResolver(
        rtsp_base_url="rtsp://127.0.0.1:8554/",
    )

    assert (
        resolver.resolve(path_name="feed-a")
        == "rtsp://127.0.0.1:8554/feed-a"
    )


@pytest.mark.parametrize(
    "path_name",
    [
        "",
        " ",
        "\t",
    ],
)
def test_rejects_empty_path_name(path_name: str) -> None:
    resolver = MediaObservationSourceResolver(
        rtsp_base_url="rtsp://127.0.0.1:8554",
    )

    with pytest.raises(
        ValueError,
        match="path_name must not be empty",
    ):
        resolver.resolve(path_name=path_name)


@pytest.mark.parametrize(
    "rtsp_base_url",
    [
        "",
        " ",
        "\t",
    ],
)
def test_rejects_empty_rtsp_base_url(
    rtsp_base_url: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="rtsp_base_url must not be empty",
    ):
        MediaObservationSourceResolver(
            rtsp_base_url=rtsp_base_url,
        )


def test_rejects_non_rtsp_base_url() -> None:
    with pytest.raises(
        ValueError,
        match="rtsp_base_url must use rtsp scheme",
    ):
        MediaObservationSourceResolver(
            rtsp_base_url="http://127.0.0.1:8554",
        )


def test_rejects_path_name_with_leading_slash() -> None:
    resolver = MediaObservationSourceResolver(
        rtsp_base_url="rtsp://127.0.0.1:8554",
    )

    with pytest.raises(
        ValueError,
        match="path_name must not start with '/'",
    ):
        resolver.resolve(path_name="/feed-a")


def test_rejects_rtsp_base_url_without_authority() -> None:
    with pytest.raises(
        ValueError,
        match="rtsp_base_url must include an authority",
    ):
        MediaObservationSourceResolver(
            rtsp_base_url="rtsp://",
        )


@pytest.mark.parametrize(
    "rtsp_base_url",
    [
        "rtsp://127.0.0.1:8554/base",
        "rtsp://127.0.0.1:8554/base/",
    ],
)
def test_rejects_rtsp_base_url_with_path(
    rtsp_base_url: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="rtsp_base_url must not include a path",
    ):
        MediaObservationSourceResolver(
            rtsp_base_url=rtsp_base_url,
        )


@pytest.mark.parametrize(
    "rtsp_base_url",
    [
        "rtsp://127.0.0.1:8554?transport=tcp",
        "rtsp://127.0.0.1:8554#media",
    ],
)
def test_rejects_rtsp_base_url_with_query_or_fragment(
    rtsp_base_url: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "rtsp_base_url must not include "
            "query or fragment"
        ),
    ):
        MediaObservationSourceResolver(
            rtsp_base_url=rtsp_base_url,
        )
