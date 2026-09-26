"""Contract tests for Signal Health alarm lifecycle coordination.

ENG-013C — Block 232C.3

The service consumes one already-detected SignalHealthTransition,
asks SignalHealthAlarmPolicy for the lifecycle decision, and delegates
alarm lifecycle operations to the existing AlarmService.

Logical alarm identity:

    (profile_id, service_id, path_name)

It must not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect or reclassify transitions;
- persist alarms directly;
- write history or evidence directly.
"""

from datetime import UTC, datetime, timedelta

from app.domain.streaming.health import HealthStatus
from app.domain.streaming.signal_health import SignalHealth
from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.domain.node_type import NodeType
from app.noc.registry.registry import NodeRegistry
from app.noc.services.alarm_service import (
    AlarmDisposition,
    AlarmService,
)
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_alarm_policy import (
    SignalHealthAlarmAction,
    SignalHealthAlarmDecision,
    SignalHealthAlarmPolicy,
)
from app.services.signal_health_transition_alarm_factory import (
    SignalHealthTransitionAlarmFactory,
)
from app.services.signal_health_transition_alarm_service import (
    SignalHealthTransitionAlarmService,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)


class MemoryRepository:
    def __init__(self):
        self.nodes = {}

    def save(self, node):
        self.nodes[node.node_id.id] = node

    def get(self, node_id):
        return self.nodes.get(node_id.id)

    def exists(self, node_id):
        return node_id.id in self.nodes

    def list_all(self):
        return tuple(self.nodes.values())

    def delete(self, node_id):
        return self.nodes.pop(node_id.id, None) is not None

    def count(self):
        return len(self.nodes)


BASE_TIME = datetime(
    2026,
    9,
    25,
    18,
    0,
    tzinfo=UTC,
)

NODE_ID = NodeId.create(
    id="streaming-node",
    name="streaming-node",
    display_name="Streaming Node",
)

INSTANCE_ID = NodeInstanceId(
    "streaming-primary"
)


def health(
    status: HealthStatus,
    *,
    profile_id: str = "impact",
    service_id: str = "impact",
    path_name: str | None = "impact",
    media_status: HealthStatus = HealthStatus.HEALTHY,
    transport_status: HealthStatus = HealthStatus.HEALTHY,
) -> SignalHealth:
    return SignalHealth(
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
        media_status=media_status,
        transport_status=transport_status,
        status=status,
    )


def transition(
    previous: HealthStatus,
    current: HealthStatus,
    kind: HealthTransitionKind,
    *,
    profile_id: str = "impact",
    service_id: str = "impact",
    path_name: str | None = "impact",
) -> SignalHealthTransition:
    return SignalHealthTransition(
        previous=health(
            previous,
            profile_id=profile_id,
            service_id=service_id,
            path_name=path_name,
        ),
        current=health(
            current,
            profile_id=profile_id,
            service_id=service_id,
            path_name=path_name,
            media_status=current,
        ),
        kind=kind,
    )


def degradation(
    *,
    profile_id: str = "impact",
    service_id: str = "impact",
    path_name: str | None = "impact",
) -> SignalHealthTransition:
    return transition(
        HealthStatus.HEALTHY,
        HealthStatus.DEGRADED,
        HealthTransitionKind.DEGRADED,
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
    )


def critical(
    *,
    profile_id: str = "impact",
    service_id: str = "impact",
    path_name: str | None = "impact",
) -> SignalHealthTransition:
    return transition(
        HealthStatus.HEALTHY,
        HealthStatus.CRITICAL,
        HealthTransitionKind.DEGRADED,
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
    )


def recovery(
    *,
    profile_id: str = "impact",
    service_id: str = "impact",
    path_name: str | None = "impact",
) -> SignalHealthTransition:
    return transition(
        HealthStatus.CRITICAL,
        HealthStatus.HEALTHY,
        HealthTransitionKind.RECOVERED,
        profile_id=profile_id,
        service_id=service_id,
        path_name=path_name,
    )


def unknown_transition() -> SignalHealthTransition:
    return transition(
        HealthStatus.UNKNOWN,
        HealthStatus.HEALTHY,
        HealthTransitionKind.UNKNOWN,
    )


class RaisePolicy(SignalHealthAlarmPolicy):
    def evaluate(
        self,
        *,
        transition,
    ) -> SignalHealthAlarmDecision:
        return SignalHealthAlarmDecision(
            action=SignalHealthAlarmAction.RAISE,
            transition=transition,
        )


class ResolvePolicy(SignalHealthAlarmPolicy):
    def evaluate(
        self,
        *,
        transition,
    ) -> SignalHealthAlarmDecision:
        return SignalHealthAlarmDecision(
            action=SignalHealthAlarmAction.RESOLVE,
            transition=transition,
        )


class KeepPolicy(SignalHealthAlarmPolicy):
    def evaluate(
        self,
        *,
        transition,
    ) -> SignalHealthAlarmDecision:
        return SignalHealthAlarmDecision(
            action=SignalHealthAlarmAction.KEEP,
            transition=transition,
        )


def make_context(
    *,
    policy: SignalHealthAlarmPolicy | None = None,
):
    repository = MemoryRepository()
    registry = NodeRegistry(repository)

    node = Node(
        node_id=NODE_ID,
        node_type=NodeType.STREAMING,
    )

    instance = node.create_instance(
        instance_id=INSTANCE_ID.value
    )

    registry.register(node)

    alarm_service = AlarmService(registry)

    service = SignalHealthTransitionAlarmService(
        alarm_service=alarm_service,
        policy=policy,
        factory=SignalHealthTransitionAlarmFactory(),
    )

    return (
        node,
        instance,
        alarm_service,
        service,
    )


def test_none_transition_is_noop():
    _, _, alarm_service, service = make_context()

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=None,
        timestamp=BASE_TIME,
    )

    assert result.transition is None
    assert result.decision.action is SignalHealthAlarmAction.NONE
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_authorized_raise_uses_existing_alarm_service():
    _, _, alarm_service, service = make_context()

    value = critical()

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME,
    )

    assert result.transition is value
    assert result.decision.action is SignalHealthAlarmAction.RAISE
    assert result.receipt is not None
    assert result.receipt.disposition is AlarmDisposition.RAISED

    assert result.alarm is result.receipt.alarm
    assert result.alarm is not None
    assert result.alarm.alarm_type == "SIGNAL_HEALTH"
    assert result.alarm.state is AlarmState.ACTIVE

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == (result.alarm,)


def test_authorized_raise_does_not_duplicate_same_identity():
    _, _, alarm_service, service = make_context()

    value = degradation()

    first = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME,
    )

    second = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert first.receipt is not None
    assert second.receipt is None
    assert second.alarm is first.alarm

    active = alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    )

    assert len(active) == 1


def test_different_signal_identities_can_have_independent_alarms():
    _, _, alarm_service, service = make_context()

    impact = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=degradation(
            profile_id="impact",
            service_id="impact",
            path_name="impact",
        ),
        timestamp=BASE_TIME,
    )

    enlace = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=degradation(
            profile_id="enlace",
            service_id="enlace",
            path_name="enlace",
        ),
        timestamp=BASE_TIME + timedelta(seconds=1),
    )

    assert impact.receipt is not None
    assert enlace.receipt is not None
    assert impact.alarm is not None
    assert enlace.alarm is not None
    assert impact.alarm.alarm_id != enlace.alarm.alarm_id

    active = alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    )

    assert len(active) == 2


def test_keep_preserves_existing_signal_alarm():
    _, _, alarm_service, raise_service = make_context(
        policy=RaisePolicy(),
    )

    opened = raise_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(),
        timestamp=BASE_TIME,
    )

    keep_service = SignalHealthTransitionAlarmService(
        alarm_service=alarm_service,
        policy=KeepPolicy(),
        factory=SignalHealthTransitionAlarmFactory(),
    )

    value = transition(
        HealthStatus.CRITICAL,
        HealthStatus.DEGRADED,
        HealthTransitionKind.IMPROVED,
    )

    result = keep_service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=value,
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert opened.alarm is not None
    assert result.decision.action is SignalHealthAlarmAction.KEEP
    assert result.receipt is None
    assert result.alarm == opened.alarm
    assert result.alarm.state is AlarmState.ACTIVE


def test_keep_without_existing_alarm_is_noop():
    _, _, alarm_service, service = make_context(
        policy=KeepPolicy(),
    )

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=unknown_transition(),
        timestamp=BASE_TIME,
    )

    assert result.decision.action is SignalHealthAlarmAction.KEEP
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_production_unknown_transition_does_not_open_alarm():
    _, _, alarm_service, service = make_context()

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=unknown_transition(),
        timestamp=BASE_TIME,
    )

    assert (
        result.transition.kind
        is HealthTransitionKind.UNKNOWN
    )
    assert (
        result.decision.action
        is SignalHealthAlarmAction.RESOLVE
    )
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_recovery_resolves_existing_active_signal_alarm():
    _, _, alarm_service, service = make_context()

    opened = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery(),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert result.decision.action is SignalHealthAlarmAction.RESOLVE
    assert result.receipt is not None
    assert result.receipt.disposition is AlarmDisposition.RESOLVED

    assert result.alarm is result.receipt.alarm
    assert result.alarm is not None
    assert result.alarm.state is AlarmState.RESOLVED

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_resolve_without_existing_alarm_is_noop():
    _, _, alarm_service, service = make_context(
        policy=ResolvePolicy(),
    )

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery(),
        timestamp=BASE_TIME,
    )

    assert result.decision.action is SignalHealthAlarmAction.RESOLVE
    assert result.alarm is None
    assert result.receipt is None

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()


def test_authorized_raise_does_not_duplicate_acknowledged_alarm():
    _, _, alarm_service, service = make_context(
        policy=RaisePolicy(),
    )

    opened = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None

    acknowledged = alarm_service.acknowledge(
        NODE_ID,
        INSTANCE_ID,
        opened.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert acknowledged.alarm.state is AlarmState.ACKNOWLEDGED

    repeated = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert repeated.receipt is None
    assert repeated.alarm is acknowledged.alarm

    active = alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    )

    assert len(active) == 1
    assert active[0].alarm_id == opened.alarm.alarm_id
    assert active[0].state is AlarmState.ACKNOWLEDGED


def test_recovery_resolves_acknowledged_alarm_preserving_ack():
    _, _, alarm_service, service = make_context()

    opened = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None

    acknowledged = alarm_service.acknowledge(
        NODE_ID,
        INSTANCE_ID,
        opened.alarm.alarm_id,
        acknowledged_by="operator",
        timestamp=BASE_TIME + timedelta(seconds=5),
    )

    assert acknowledged.alarm.state is AlarmState.ACKNOWLEDGED
    assert acknowledged.alarm.acknowledged is True

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery(),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert result.decision.action is SignalHealthAlarmAction.RESOLVE
    assert result.receipt is not None
    assert result.receipt.disposition is AlarmDisposition.RESOLVED

    assert result.alarm is not None
    assert result.alarm.state is AlarmState.RESOLVED
    assert result.alarm.alarm_id == opened.alarm.alarm_id

    assert result.alarm.acknowledged is True
    assert result.alarm.acknowledged_by == "operator"
    assert result.alarm.acknowledged_at == (
        BASE_TIME + timedelta(seconds=5)
    )


def test_recovery_only_resolves_matching_signal_identity():
    _, _, alarm_service, service = make_context()

    impact = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(
            profile_id="impact",
            service_id="impact",
            path_name="impact",
        ),
        timestamp=BASE_TIME,
    )

    enlace = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(
            profile_id="enlace",
            service_id="enlace",
            path_name="enlace",
        ),
        timestamp=BASE_TIME + timedelta(seconds=1),
    )

    assert impact.alarm is not None
    assert enlace.alarm is not None

    recovered = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=recovery(
            profile_id="impact",
            service_id="impact",
            path_name="impact",
        ),
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert recovered.receipt is not None
    assert recovered.receipt.disposition is AlarmDisposition.RESOLVED
    assert recovered.alarm is not None
    assert recovered.alarm.alarm_id == impact.alarm.alarm_id

    active = alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    )

    assert len(active) == 1
    assert active[0].alarm_id == enlace.alarm.alarm_id
    assert active[0].attributes is not None
    assert active[0].attributes["profile_id"] == "enlace"


def test_service_exposes_dependencies():
    _, _, alarm_service, service = make_context()

    assert service.alarm_service is alarm_service
    assert isinstance(
        service.policy,
        SignalHealthAlarmPolicy,
    )
    assert isinstance(
        service.factory,
        SignalHealthTransitionAlarmFactory,
    )



def test_unknown_to_healthy_resolves_existing_signal_alarm():
    """Confirmed HEALTHY closes an existing alarm across UNKNOWN.

    The Signal transition remains UNKNOWN.  Alarm lifecycle must still
    resolve the matching existing alarm once current Signal Health is
    explicitly HEALTHY.
    """
    _, _, alarm_service, service = make_context()

    opened = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=critical(),
        timestamp=BASE_TIME,
    )

    assert opened.alarm is not None
    assert opened.alarm.state is AlarmState.ACTIVE

    healthy_after_unknown = unknown_transition()

    assert (
        healthy_after_unknown.kind
        is HealthTransitionKind.UNKNOWN
    )
    assert (
        healthy_after_unknown.current.status
        is HealthStatus.HEALTHY
    )

    result = service.process_transition(
        node_id=NODE_ID,
        instance_id=INSTANCE_ID,
        transition=healthy_after_unknown,
        timestamp=BASE_TIME + timedelta(seconds=10),
    )

    assert (
        result.decision.action
        is SignalHealthAlarmAction.RESOLVE
    )
    assert result.receipt is not None
    assert (
        result.receipt.disposition
        is AlarmDisposition.RESOLVED
    )
    assert result.alarm is not None
    assert result.alarm.state is AlarmState.RESOLVED
    assert result.alarm.alarm_id == opened.alarm.alarm_id

    assert alarm_service.active(
        NODE_ID,
        INSTANCE_ID,
    ) == ()
