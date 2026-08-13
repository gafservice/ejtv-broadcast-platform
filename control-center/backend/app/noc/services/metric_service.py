"""Metric coordination service for the NOC.

ENG-013B — Node SDK
NCS reference: 16-NODE-METRIC.md

MetricService coordinates reception of MetricSample objects for
registered NodeInstances.

The service maintains the current metric state of an instance.
Historical telemetry persistence belongs to another layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.domain.node_metric import (
    MetricSample,
    NodeMetric,
)
from app.noc.registry.registry import NodeRegistry


class MetricServiceError(Exception):
    """Base exception for MetricService operations."""


class NodeInstanceNotFoundError(MetricServiceError):
    """Raised when a metric targets an unknown NodeInstance."""


class MetricRejectedError(MetricServiceError):
    """Base exception for metric samples that cannot be accepted."""


class DuplicateMetricError(MetricRejectedError):
    """Raised when the same metric sample is received again."""


class StaleMetricError(MetricRejectedError):
    """Raised when an older metric sample is received."""


class MetricDisposition(str, Enum):
    """Classification of an accepted metric sample."""

    FIRST = "FIRST"
    ADDED = "ADDED"
    REPLACED = "REPLACED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MetricReceipt:
    """Result of processing an accepted MetricSample."""

    disposition: MetricDisposition
    sample: MetricSample
    metrics: NodeMetric
    previous: MetricSample | None = None

    @property
    def replaced(self) -> bool:
        return self.disposition is MetricDisposition.REPLACED


class MetricService:
    """Coordinate current metric state for registered NodeInstances.

    Rules implemented here:

    - the logical Node must already be registered;
    - the NodeInstance must belong to that Node;
    - MetricSample is the atomic input unit;
    - metric names are compared case-insensitively;
    - only the latest sample for each metric is retained;
    - duplicate samples are rejected;
    - older samples are rejected;
    - different metrics coexist;
    - accepted state changes are persisted through NodeRepository.

    MetricService does not calculate metrics and does not retain
    historical telemetry.
    """

    def __init__(
        self,
        registry: NodeRegistry,
    ) -> None:
        if not isinstance(registry, NodeRegistry):
            raise TypeError(
                "registry must be a NodeRegistry"
            )

        self._registry = registry

    @property
    def registry(self) -> NodeRegistry:
        return self._registry

    def receive(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        sample: MetricSample,
    ) -> MetricReceipt:
        """Accept one current metric sample for a NodeInstance."""
        self._require_node_id(node_id)
        self._require_instance_id(instance_id)
        self._require_sample(sample)

        node = self._registry.require(
            node_id
        )

        instance = self._find_instance(
            node.instances,
            instance_id,
        )

        if instance is None:
            raise NodeInstanceNotFoundError(
                f"NodeInstance {instance_id!s} is not registered "
                f"under Node {node_id.id!r}"
            )

        current = self._current_samples(
            instance
        )

        previous = self._find_metric(
            current,
            sample.metric,
        )

        if previous is None:
            disposition = (
                MetricDisposition.FIRST
                if not current
                else MetricDisposition.ADDED
            )

            updated = current + (
                sample,
            )

        else:
            self._validate_replacement(
                previous,
                sample,
            )

            disposition = (
                MetricDisposition.REPLACED
            )

            updated = tuple(
                sample
                if existing.metric.casefold()
                == sample.metric.casefold()
                else existing
                for existing in current
            )

        metrics = NodeMetric(
            samples=updated
        )

        # NodeInstance stores current metric samples. SnapshotService
        # composes them into the canonical NodeMetric representation.
        instance.metrics = metrics.samples

        self._registry.repository.save(
            node
        )

        return MetricReceipt(
            disposition=disposition,
            sample=sample,
            metrics=metrics,
            previous=previous,
        )

    def current(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> NodeMetric:
        """Return current metric state for a NodeInstance."""
        self._require_node_id(node_id)
        self._require_instance_id(instance_id)

        node = self._registry.require(
            node_id
        )

        instance = self._find_instance(
            node.instances,
            instance_id,
        )

        if instance is None:
            raise NodeInstanceNotFoundError(
                f"NodeInstance {instance_id!s} is not registered "
                f"under Node {node_id.id!r}"
            )

        return NodeMetric(
            samples=self._current_samples(
                instance
            )
        )

    @staticmethod
    def _current_samples(
        instance: NodeInstance,
    ) -> tuple[MetricSample, ...]:
        value = getattr(
            instance,
            "metrics",
            (),
        )

        if value is None:
            return ()

        if isinstance(value, NodeMetric):
            return value.samples

        if not isinstance(value, tuple):
            raise MetricServiceError(
                "NodeInstance.metrics must be a tuple or NodeMetric"
            )

        samples: list[MetricSample] = []

        for item in value:
            if isinstance(item, MetricSample):
                samples.append(
                    item
                )

            elif isinstance(item, NodeMetric):
                samples.extend(
                    item.samples
                )

            else:
                raise MetricServiceError(
                    "NodeInstance.metrics must contain "
                    "MetricSample or NodeMetric objects"
                )

        # Reuse the domain aggregate to enforce uniqueness.
        return NodeMetric(
            samples=tuple(samples)
        ).samples

    @staticmethod
    def _find_metric(
        samples: tuple[MetricSample, ...],
        metric: str,
    ) -> MetricSample | None:
        canonical = metric.casefold()

        for sample in samples:
            if sample.metric.casefold() == canonical:
                return sample

        return None

    @staticmethod
    def _validate_replacement(
        previous: MetricSample,
        incoming: MetricSample,
    ) -> None:
        if incoming == previous:
            raise DuplicateMetricError(
                f"Metric sample {incoming.metric!r} "
                "has already been received"
            )

        if incoming.timestamp < previous.timestamp:
            raise StaleMetricError(
                f"Metric sample {incoming.metric!r} precedes "
                "the latest accepted sample"
            )

        if incoming.timestamp == previous.timestamp:
            raise DuplicateMetricError(
                f"Metric {incoming.metric!r} already has a sample "
                "for this timestamp"
            )

    @staticmethod
    def _find_instance(
        instances: tuple[NodeInstance, ...],
        instance_id: NodeInstanceId,
    ) -> NodeInstance | None:
        for instance in instances:
            if instance.instance_id == instance_id:
                return instance

        return None

    @staticmethod
    def _require_node_id(
        node_id: NodeId,
    ) -> None:
        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

    @staticmethod
    def _require_instance_id(
        instance_id: NodeInstanceId,
    ) -> None:
        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

    @staticmethod
    def _require_sample(
        sample: MetricSample,
    ) -> None:
        if not isinstance(
            sample,
            MetricSample,
        ):
            raise TypeError(
                "sample must be a MetricSample"
            )
