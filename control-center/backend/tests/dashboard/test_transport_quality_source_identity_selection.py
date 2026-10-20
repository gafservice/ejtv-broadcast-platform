"""Conservative source-identity observation selection contract.

ENG-013C — 235E.30A — 9A.68.7D.30A.

Selection only. No RTT attribution or Health evaluation.
"""

from datetime import UTC, datetime

import pytest

from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.streaming.media_observation import EvidenceAvailability
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)


OBSERVED_AT = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)


def observation(
    source_id,
    *,
    service_id="impact",
    path_name="impact",
    source_type="srtConn",
):
    return TransportQualityObservation(
        service_id=service_id,
        path_name=path_name,
        source_type=source_type,
        source_id=source_id,
        observed_at=OBSERVED_AT,
        availability=EvidenceAvailability.UNAVAILABLE,
    )


def select(observations, source_id):
    return (
        IncomingTransportCardsRenderer
        ._select_transport_quality_observation(
            observations,
            path_name="impact",
            source_type="srtConn",
            source_id=source_id,
        )
    )


@pytest.mark.parametrize(
    "selected_id,observed_id,expected_match",
    (
        ("publisher-A", "publisher-A", True),
        ("publisher-B", "publisher-A", False),
        ("publisher-A", None, False),
        (None, "publisher-A", False),
        (None, None, True),
    ),
)
def test_source_identity_compatibility(
    selected_id,
    observed_id,
    expected_match,
):
    candidate = observation(observed_id)

    selected = select((candidate,), selected_id)

    if expected_match:
        assert selected is candidate
    else:
        assert selected is None


def test_rejects_ambiguous_same_source_identity():
    observations = (
        observation("publisher-A", service_id="service-a"),
        observation("publisher-A", service_id="service-b"),
    )

    assert select(observations, "publisher-A") is None


def test_rejects_old_source_after_replacement():
    old = observation("publisher-A")
    current = observation("publisher-B")

    assert select((old,), "publisher-B") is None
    assert select((old, current), "publisher-B") is current


def test_rejects_missing_identity_when_selected_source_is_known():
    candidate = observation(None)

    assert select((candidate,), "publisher-A") is None


def test_rejects_known_identity_when_selected_source_is_unknown():
    candidate = observation("publisher-A")

    assert select((candidate,), None) is None


def test_rejects_ambiguous_unknown_identity():
    observations = (
        observation(None, service_id="service-a"),
        observation(None, service_id="service-b"),
    )

    assert select(observations, None) is None
