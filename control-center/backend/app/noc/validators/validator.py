"""NCS contract validation.

ENG-013B — Node SDK
NCS reference: 28-VALIDATION-RULES.md

Domain entities enforce their own local invariants during construction.
This module performs contract-level and cross-entity validation without
modifying the validated information.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_snapshot import NodeSnapshot


class ValidationStatus(str, Enum):
    """Global result of an NCS validation."""

    VALID = "VALID"
    INVALID = "INVALID"
    WARNING = "WARNING"

    def __str__(self) -> str:
        return self.value


class ValidationLevel(str, Enum):
    """Validation levels defined by NCS v1.0.0."""

    SYNTACTIC = "SYNTACTIC"
    STRUCTURAL = "STRUCTURAL"
    SEMANTIC = "SEMANTIC"
    RESTRICTION = "RESTRICTION"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Single validation error or warning."""

    code: str
    message: str
    level: ValidationLevel
    field: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise TypeError(
                "ValidationIssue.code must be a string"
            )

        if not self.code.strip():
            raise ValueError(
                "ValidationIssue.code must not be empty"
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "ValidationIssue.message must be a string"
            )

        if not self.message.strip():
            raise ValueError(
                "ValidationIssue.message must not be empty"
            )

        if not isinstance(self.level, ValidationLevel):
            raise TypeError(
                "ValidationIssue.level must be a ValidationLevel"
            )

        object.__setattr__(
            self,
            "code",
            self.code.strip().upper(),
        )

        object.__setattr__(
            self,
            "message",
            self.message.strip(),
        )

        if self.field is not None:
            if not isinstance(self.field, str):
                raise TypeError(
                    "ValidationIssue.field must be a string or None"
                )

            normalized = self.field.strip()

            object.__setattr__(
                self,
                "field",
                normalized or None,
            )


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result produced by an NCS contract validation."""

    status: ValidationStatus
    errors: tuple[ValidationIssue, ...]
    warnings: tuple[ValidationIssue, ...]
    validated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.status, ValidationStatus):
            raise TypeError(
                "ValidationResult.status must be a ValidationStatus"
            )

        if not isinstance(self.errors, tuple):
            raise TypeError(
                "ValidationResult.errors must be a tuple"
            )

        if not isinstance(self.warnings, tuple):
            raise TypeError(
                "ValidationResult.warnings must be a tuple"
            )

        for issue in (*self.errors, *self.warnings):
            if not isinstance(issue, ValidationIssue):
                raise TypeError(
                    "ValidationResult issues must be ValidationIssue objects"
                )

        if not isinstance(self.validated_at, datetime):
            raise TypeError(
                "ValidationResult.validated_at must be a datetime"
            )

        if self.validated_at.tzinfo is None:
            raise ValueError(
                "ValidationResult.validated_at must be timezone-aware"
            )

        if self.validated_at.utcoffset() != timezone.utc.utcoffset(
            self.validated_at
        ):
            raise ValueError(
                "ValidationResult.validated_at must be UTC"
            )

    @property
    def is_valid(self) -> bool:
        """Return whether no contract errors were found."""
        return self.status in {
            ValidationStatus.VALID,
            ValidationStatus.WARNING,
        }

    @property
    def is_invalid(self) -> bool:
        return self.status is ValidationStatus.INVALID

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


class ContractValidator:
    """Validate NCS domain objects without modifying them."""

    def validate(self, value: Any) -> ValidationResult:
        """Validate a supported NCS domain object.

        NodeSnapshot is the first complete contract object supported
        by ENG-013B. Additional object validators may be incorporated
        without changing this public interface.
        """
        if isinstance(value, NodeSnapshot):
            return self.validate_snapshot(value)

        return self._result(
            errors=(
                ValidationIssue(
                    code="UNSUPPORTED_TYPE",
                    message=(
                        "Object type is not supported by "
                        "the NCS contract validator"
                    ),
                    level=ValidationLevel.STRUCTURAL,
                    field=None,
                ),
            )
        )

    def validate_snapshot(
        self,
        snapshot: NodeSnapshot,
    ) -> ValidationResult:
        """Validate NodeSnapshot contract coherence."""
        if not isinstance(snapshot, NodeSnapshot):
            return self._result(
                errors=(
                    ValidationIssue(
                        code="SNAPSHOT_TYPE",
                        message=(
                            "Value must be a NodeSnapshot"
                        ),
                        level=ValidationLevel.STRUCTURAL,
                        field="snapshot",
                    ),
                )
            )

        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        self._validate_snapshot_identity(
            snapshot,
            errors,
        )

        self._validate_snapshot_info(
            snapshot,
            errors,
        )

        self._validate_snapshot_alarms(
            snapshot,
            errors,
        )

        self._validate_snapshot_heartbeat(
            snapshot,
            errors,
        )

        return self._result(
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _validate_snapshot_identity(
        snapshot: NodeSnapshot,
        errors: list[ValidationIssue],
    ) -> None:
        from app.noc.domain.node_id import NodeId
        from app.noc.domain.node_instance import NodeInstanceId
        from app.noc.domain.node_type import NodeType

        if not isinstance(snapshot.node_id, NodeId):
            errors.append(
                ValidationIssue(
                    code="SNAPSHOT_NODE_ID",
                    message=(
                        "Snapshot node_id must be a NodeId"
                    ),
                    level=ValidationLevel.STRUCTURAL,
                    field="node_id",
                )
            )

        if not isinstance(snapshot.node_type, NodeType):
            errors.append(
                ValidationIssue(
                    code="SNAPSHOT_NODE_TYPE",
                    message=(
                        "Snapshot node_type must be a NodeType"
                    ),
                    level=ValidationLevel.SEMANTIC,
                    field="node_type",
                )
            )

        if not isinstance(
            snapshot.instance_id,
            NodeInstanceId,
        ):
            errors.append(
                ValidationIssue(
                    code="SNAPSHOT_INSTANCE_ID",
                    message=(
                        "Snapshot instance_id must be "
                        "a NodeInstanceId"
                    ),
                    level=ValidationLevel.STRUCTURAL,
                    field="instance_id",
                )
            )

        if not ContractValidator._is_utc_datetime(
            snapshot.snapshot_timestamp
        ):
            errors.append(
                ValidationIssue(
                    code="SNAPSHOT_TIMESTAMP",
                    message=(
                        "Snapshot timestamp must be "
                        "a timezone-aware UTC datetime"
                    ),
                    level=ValidationLevel.RESTRICTION,
                    field="snapshot_timestamp",
                )
            )

    @staticmethod
    def _validate_snapshot_info(
        snapshot: NodeSnapshot,
        errors: list[ValidationIssue],
    ) -> None:
        if snapshot.info is None:
            return

        if snapshot.info.instance_id != snapshot.instance_id:
            errors.append(
                ValidationIssue(
                    code="SNAPSHOT_INFO_INSTANCE",
                    message=(
                        "NodeInfo belongs to a different "
                        "NodeInstance"
                    ),
                    level=ValidationLevel.RESTRICTION,
                    field="info.instance_id",
                )
            )

    @staticmethod
    def _validate_snapshot_alarms(
        snapshot: NodeSnapshot,
        errors: list[ValidationIssue],
    ) -> None:
        if snapshot.alarms is None:
            return

        for alarm in snapshot.alarms.alarms:
            if alarm.source != snapshot.instance_id:
                errors.append(
                    ValidationIssue(
                        code="SNAPSHOT_ALARM_INSTANCE",
                        message=(
                            "Alarm belongs to a different "
                            "NodeInstance"
                        ),
                        level=ValidationLevel.RESTRICTION,
                        field="alarms",
                    )
                )

            if alarm.state not in {
                AlarmState.ACTIVE,
                AlarmState.ACKNOWLEDGED,
            }:
                errors.append(
                    ValidationIssue(
                        code="SNAPSHOT_ALARM_STATE",
                        message=(
                            "Snapshot may contain only active "
                            "or acknowledged alarms"
                        ),
                        level=ValidationLevel.SEMANTIC,
                        field="alarms",
                    )
                )

    @staticmethod
    def _validate_snapshot_heartbeat(
        snapshot: NodeSnapshot,
        errors: list[ValidationIssue],
    ) -> None:
        if (
            snapshot.heartbeat is None
            or snapshot.heartbeat.latest is None
        ):
            return

        if not snapshot.heartbeat.belongs_to(
            snapshot.instance_id
        ):
            errors.append(
                ValidationIssue(
                    code="SNAPSHOT_HEARTBEAT_INSTANCE",
                    message=(
                        "Heartbeat belongs to a different "
                        "NodeInstance"
                    ),
                    level=ValidationLevel.RESTRICTION,
                    field="heartbeat.latest.instance_id",
                )
            )

    @staticmethod
    def _is_utc_datetime(value: object) -> bool:
        if not isinstance(value, datetime):
            return False

        if value.tzinfo is None:
            return False

        offset = value.utcoffset()

        return (
            offset is not None
            and offset.total_seconds() == 0
        )

    @staticmethod
    def _result(
        *,
        errors: tuple[ValidationIssue, ...] = (),
        warnings: tuple[ValidationIssue, ...] = (),
    ) -> ValidationResult:
        if errors:
            status = ValidationStatus.INVALID
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.VALID

        return ValidationResult(
            status=status,
            errors=errors,
            warnings=warnings,
            validated_at=datetime.now(timezone.utc),
        )
