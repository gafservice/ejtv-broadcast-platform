"""Tests for the NCS ContractValidator.

ENG-013B — Node SDK
NCS reference: 28-VALIDATION-RULES.md
"""

from datetime import datetime, timezone

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_snapshot import NodeSnapshot
from app.noc.domain.node_type import NodeType
from app.noc.validators.validator import (
    ContractValidator,
    ValidationLevel,
    ValidationStatus,
)


def make_snapshot() -> NodeSnapshot:
    return NodeSnapshot(
        node_id=NodeId.create(
            id="streaming-core",
            name="streaming",
            display_name="Streaming Core",
        ),
        node_type=NodeType.STREAMING,
        instance_id=NodeInstanceId(
            "streaming-primary"
        ),
        snapshot_timestamp=datetime.now(
            timezone.utc
        ),
    )


def test_valid_snapshot_is_valid() -> None:
    validator = ContractValidator()

    result = validator.validate(
        make_snapshot()
    )

    assert result.status is ValidationStatus.VALID
    assert result.is_valid is True
    assert result.is_invalid is False
    assert result.errors == ()
    assert result.warnings == ()


def test_minimal_snapshot_is_valid() -> None:
    """NCS permits omission of non-applicable components."""
    validator = ContractValidator()

    result = validator.validate_snapshot(
        make_snapshot()
    )

    assert result.status is ValidationStatus.VALID


def test_validation_result_uses_utc_timestamp() -> None:
    result = ContractValidator().validate(
        make_snapshot()
    )

    assert result.validated_at.tzinfo is not None
    assert (
        result.validated_at.utcoffset().total_seconds()
        == 0
    )


def test_unsupported_object_is_invalid() -> None:
    result = ContractValidator().validate(
        {"node": "streaming-core"}
    )

    assert result.status is ValidationStatus.INVALID
    assert len(result.errors) == 1
    assert result.errors[0].code == "UNSUPPORTED_TYPE"
    assert (
        result.errors[0].level
        is ValidationLevel.STRUCTURAL
    )


def test_validate_snapshot_rejects_wrong_type() -> None:
    result = ContractValidator().validate_snapshot(
        "snapshot"  # type: ignore[arg-type]
    )

    assert result.status is ValidationStatus.INVALID
    assert result.errors[0].code == "SNAPSHOT_TYPE"


def test_validator_detects_invalid_node_type() -> None:
    snapshot = make_snapshot()

    # Deliberately corrupt the frozen object to simulate
    # malformed/deserialized external data.
    object.__setattr__(
        snapshot,
        "node_type",
        "STREAMING",
    )

    result = ContractValidator().validate_snapshot(
        snapshot
    )

    assert result.status is ValidationStatus.INVALID

    assert any(
        issue.code == "SNAPSHOT_NODE_TYPE"
        for issue in result.errors
    )


def test_validator_detects_invalid_instance_id() -> None:
    snapshot = make_snapshot()

    object.__setattr__(
        snapshot,
        "instance_id",
        "streaming-primary",
    )

    result = ContractValidator().validate_snapshot(
        snapshot
    )

    assert result.status is ValidationStatus.INVALID

    assert any(
        issue.code == "SNAPSHOT_INSTANCE_ID"
        for issue in result.errors
    )


def test_validator_detects_invalid_timestamp() -> None:
    snapshot = make_snapshot()

    object.__setattr__(
        snapshot,
        "snapshot_timestamp",
        datetime(2026, 8, 12, 12, 0),
    )

    result = ContractValidator().validate_snapshot(
        snapshot
    )

    assert result.status is ValidationStatus.INVALID

    assert any(
        issue.code == "SNAPSHOT_TIMESTAMP"
        for issue in result.errors
    )


def test_validation_does_not_modify_snapshot() -> None:
    snapshot = make_snapshot()

    original_node_id = snapshot.node_id
    original_node_type = snapshot.node_type
    original_instance_id = snapshot.instance_id
    original_timestamp = snapshot.snapshot_timestamp

    ContractValidator().validate_snapshot(
        snapshot
    )

    assert snapshot.node_id is original_node_id
    assert snapshot.node_type is original_node_type
    assert snapshot.instance_id is original_instance_id
    assert snapshot.snapshot_timestamp is original_timestamp


def test_repeated_validation_is_reproducible() -> None:
    snapshot = make_snapshot()
    validator = ContractValidator()

    first = validator.validate_snapshot(
        snapshot
    )

    second = validator.validate_snapshot(
        snapshot
    )

    assert first.status == second.status
    assert first.errors == second.errors
    assert first.warnings == second.warnings


def test_validation_status_string_representation() -> None:
    assert str(ValidationStatus.VALID) == "VALID"


def test_validation_level_string_representation() -> None:
    assert (
        str(ValidationLevel.RESTRICTION)
        == "RESTRICTION"
    )
