"""Source identity contract for Transport Quality observations."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)


OBSERVED_AT = datetime(2026, 10, 20, 19, 0, tzinfo=UTC)


def make_observation(**overrides):
    kwargs = {
        "service_id": "impact-main",
        "path_name": "impact",
        "source_type": "srtConn",
        "observed_at": OBSERVED_AT,
        "availability": EvidenceAvailability.UNAVAILABLE,
    }

    kwargs.update(overrides)

    return TransportQualityObservation(**kwargs)


def test_source_identity_is_optional_for_legacy_observations():
    observation = make_observation()

    assert observation.source_id is None


def test_preserves_srt_publisher_source_identity():
    observation = make_observation(source_id="publisher-A")

    assert observation.source_id == "publisher-A"


def test_preserves_udp_source_identity():
    observation = make_observation(
        source_type="udpSource",
        source_id="udp-source-1",
    )

    assert observation.source_id == "udp-source-1"


def test_preserves_missing_source_identity():
    observation = make_observation(source_id=None)

    assert observation.source_id is None


@pytest.mark.parametrize(
    "invalid",
    ("", " ", "\t", "\n"),
)
def test_rejects_blank_source_identity(invalid):
    with pytest.raises(ValueError, match="source_id"):
        make_observation(source_id=invalid)


@pytest.mark.parametrize(
    "invalid",
    (0, 123, True, [], {}),
)
def test_rejects_non_string_source_identity(invalid):
    with pytest.raises(
        TypeError,
        match="source_id must be a str",
    ):
        make_observation(source_id=invalid)


def test_normalizes_source_identity_whitespace():
    observation = make_observation(
        source_id="  publisher-A  "
    )

    assert observation.source_id == "publisher-A"


def test_source_identity_is_immutable():
    observation = make_observation(
        source_id="publisher-A"
    )

    with pytest.raises(FrozenInstanceError):
        observation.source_id = "publisher-B"
