"""Conservative Transport Quality observation selection contract.

ENG-013C — 235E.30A — 9A.68.7D.8.

Selection only:
- no metric attribution;
- no Health evaluation;
- no arbitrary choice among ambiguous observations.
"""

from datetime import datetime, timezone

import pytest

from app.dashboard.renderers.incoming_transport_cards_renderer import (
    IncomingTransportCardsRenderer,
)
from app.domain.streaming.media_observation import (
    EvidenceAvailability,
)
from app.domain.streaming.transport_quality_observation import (
    TransportQualityObservation,
)


OBSERVED_AT = datetime(
    2026,
    10,
    20,
    18,
    0,
    tzinfo=timezone.utc,
)


def observation(
    service_id: str,
    path_name: str,
    source_type: str,
) -> TransportQualityObservation:
    return TransportQualityObservation(
        service_id=service_id,
        path_name=path_name,
        source_type=source_type,
        observed_at=OBSERVED_AT,
        availability=EvidenceAvailability.UNAVAILABLE,
    )


@pytest.mark.parametrize(
    "selected_path,source_type,expected_service",
    (
        ("ejtv", "udpSource", "ejtv"),
        ("enlace", "udpSource", "enlace"),
        ("impact", "srtConn", "impact"),
    ),
)
def test_selects_unique_matching_observation(
    selected_path,
    source_type,
    expected_service,
):
    observations = (
        observation("ejtv", "ejtv", "udpSource"),
        observation("enlace", "enlace", "udpSource"),
        observation("impact", "impact", "srtConn"),
    )

    selected = (
        IncomingTransportCardsRenderer._select_transport_quality_observation(
            observations,
            path_name=selected_path,
            source_type=source_type,
        )
    )

    assert selected is next(
        item
        for item in observations
        if item.service_id == expected_service
    )


@pytest.mark.parametrize(
    "selected_path,source_type",
    (
        ("missing", "udpSource"),
        ("ejtv", "srtConn"),
        ("impact", "udpSource"),
        ("ejtv", None),
    ),
)
def test_rejects_missing_or_incompatible_observation(
    selected_path,
    source_type,
):
    observations = (
        observation("ejtv", "ejtv", "udpSource"),
        observation("impact", "impact", "srtConn"),
    )

    selected = (
        IncomingTransportCardsRenderer._select_transport_quality_observation(
            observations,
            path_name=selected_path,
            source_type=source_type,
        )
    )

    assert selected is None


def test_rejects_ambiguous_same_path_and_source_type():
    observations = (
        observation("service-a", "ejtv", "udpSource"),
        observation("service-b", "ejtv", "udpSource"),
    )

    selected = (
        IncomingTransportCardsRenderer._select_transport_quality_observation(
            observations,
            path_name="ejtv",
            source_type="udpSource",
        )
    )

    assert selected is None


def test_rejects_duplicate_observation_identity():
    observations = (
        observation("ejtv", "ejtv", "udpSource"),
        observation("ejtv", "ejtv", "udpSource"),
    )

    selected = (
        IncomingTransportCardsRenderer._select_transport_quality_observation(
            observations,
            path_name="ejtv",
            source_type="udpSource",
        )
    )

    assert selected is None


def test_does_not_choose_by_order():
    observations = (
        observation("service-a", "ejtv", "udpSource"),
        observation("service-b", "ejtv", "udpSource"),
    )

    for candidates in (
        observations,
        tuple(reversed(observations)),
    ):
        selected = (
            IncomingTransportCardsRenderer._select_transport_quality_observation(
                candidates,
                path_name="ejtv",
                source_type="udpSource",
            )
        )

        assert selected is None
