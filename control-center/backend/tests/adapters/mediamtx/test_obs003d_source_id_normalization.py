"""OBS-003D — MediaMTX source identity normalization contract."""

import pytest

from app.adapters.mediamtx.adapter import MediaMTXAdapter


@pytest.mark.parametrize(
    "source_id, expected",
    (
        ("publisher-001", "publisher-001"),
        ("", None),
        ("   ", None),
        (None, None),
        (123, None),
    ),
)
def test_source_identity_normalization(source_id, expected):
    source = MediaMTXAdapter._parse_source(
        {
            "type": "srtConn",
            "id": source_id,
        }
    )

    assert source is not None
    assert source.source_type == "srtConn"
    assert source.source_id == expected


def test_missing_source_identity_is_none():
    source = MediaMTXAdapter._parse_source(
        {"type": "udpSource"}
    )

    assert source is not None
    assert source.source_id is None
