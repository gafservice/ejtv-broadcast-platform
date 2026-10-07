from pathlib import Path

import pytest

from app.noc.infrastructure.node_incoming_origin_loader import (
    NodeIncomingOriginLoader,
)


def test_missing_incoming_origins_returns_empty_mapping() -> None:
    origins = NodeIncomingOriginLoader().from_mapping(
        {
            "node": "node-01",
        }
    )

    assert origins == {}


def test_loads_expected_origin_by_path() -> None:
    origins = NodeIncomingOriginLoader().from_mapping(
        {
            "node": "node-01",
            "incoming_origins": [
                {
                    "path_name": "ejtv",
                    "expected_remote_address": "10.0.18.51:3000",
                },
                {
                    "path_name": "enlace",
                    "expected_remote_address": "10.0.18.56:3000",
                },
            ],
        }
    )

    assert origins == {
        "ejtv": "10.0.18.51:3000",
        "enlace": "10.0.18.56:3000",
    }


def test_normalizes_path_and_address() -> None:
    origins = NodeIncomingOriginLoader().from_mapping(
        {
            "incoming_origins": [
                {
                    "path_name": "  future-service  ",
                    "expected_remote_address": "  192.0.2.10:5000  ",
                },
            ],
        }
    )

    assert origins == {
        "future-service": "192.0.2.10:5000",
    }


@pytest.mark.parametrize(
    "incoming_origins",
    (
        {},
        "invalid",
        123,
    ),
)
def test_incoming_origins_must_be_list(
    incoming_origins,
) -> None:
    with pytest.raises(TypeError):
        NodeIncomingOriginLoader().from_mapping(
            {
                "incoming_origins": incoming_origins,
            }
        )


@pytest.mark.parametrize(
    (
        "entry",
        "expected_exception",
    ),
    (
        (
            {
                "expected_remote_address": "10.0.18.51:3000",
            },
            ValueError,
        ),
        (
            {
                "path_name": "   ",
                "expected_remote_address": "10.0.18.51:3000",
            },
            ValueError,
        ),
        (
            {
                "path_name": 123,
                "expected_remote_address": "10.0.18.51:3000",
            },
            TypeError,
        ),
        (
            {
                "path_name": "ejtv",
            },
            ValueError,
        ),
        (
            {
                "path_name": "ejtv",
                "expected_remote_address": "   ",
            },
            ValueError,
        ),
        (
            {
                "path_name": "ejtv",
                "expected_remote_address": 123,
            },
            TypeError,
        ),
    ),
)
def test_rejects_invalid_origin_entries(
    entry,
    expected_exception,
) -> None:
    with pytest.raises(expected_exception):
        NodeIncomingOriginLoader().from_mapping(
            {
                "incoming_origins": [
                    entry,
                ],
            }
        )


def test_rejects_duplicate_path_name() -> None:
    with pytest.raises(ValueError):
        NodeIncomingOriginLoader().from_mapping(
            {
                "incoming_origins": [
                    {
                        "path_name": "ejtv",
                        "expected_remote_address": "10.0.18.51:3000",
                    },
                    {
                        "path_name": "ejtv",
                        "expected_remote_address": "192.0.2.20:3000",
                    },
                ],
            }
        )


def test_loads_yaml_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "node.yaml"

    path.write_text(
        """
node: node-01

incoming_origins:
  - path_name: ejtv
    expected_remote_address: "10.0.18.51:3000"

  - path_name: enlace
    expected_remote_address: "10.0.18.56:3000"
""".strip(),
        encoding="utf-8",
    )

    origins = NodeIncomingOriginLoader().load(path)

    assert origins == {
        "ejtv": "10.0.18.51:3000",
        "enlace": "10.0.18.56:3000",
    }


def test_missing_file_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        NodeIncomingOriginLoader().load(
            tmp_path / "missing.yaml"
        )


def test_path_argument_must_be_valid_type() -> None:
    with pytest.raises(TypeError):
        NodeIncomingOriginLoader().load(
            123  # type: ignore[arg-type]
        )


def test_real_ejtv_node_declares_expected_incoming_origins() -> None:
    origins = NodeIncomingOriginLoader().load(
        Path("../config/nodes/ejtv-01.yaml")
    )

    assert origins["ejtv"] == "10.0.18.51:3000"
    assert origins["enlace"] == "10.0.18.56:3000"
