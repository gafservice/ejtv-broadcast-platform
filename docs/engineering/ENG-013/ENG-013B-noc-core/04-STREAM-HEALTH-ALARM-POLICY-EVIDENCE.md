# ENG-013B - Stream Health Alarm Policy Evidence

## Scope

Validation evidence for:

`Block 5 - ALARM POLICY INTEGRATION`

Block 5 connects already-detected semantic Stream Health transitions with
the existing NOC alarm lifecycle without converting Health severity directly
into operator-facing alarms.

The governing architectural rule remains:

```text
Stream Health determines state.
Events record transitions and operational facts.
Alarm Policies determine which conditions require intervention.
Alarms manage the lifecycle of that intervention.
History/Evidence preserves operational memory.
```

Block 5 does not redefine Stream Health evaluation, temporal stabilization,
transition detection, Events, or the existing NOC alarm lifecycle.

## Architectural boundary

The implemented flow is:

```text
RAW TELEMETRY
    |
    v
NORMALIZATION
    |
    v
STREAM HEALTH
    |
    v
TEMPORAL HEALTH
    |
    v
STREAMING HEALTH TRANSITION
    |
    +------------------------------+
    |                              |
    v                              v
BLOCK 4                         BLOCK 5
EVENT SERVICE                  ALARM POLICY
    |                              |
    v                              v
EVENT                    NONE / RAISE / KEEP / RESOLVE
                                   |
                                   v
                              ALARM FACTORY
                                   |
                                   v
                           EXISTING AlarmService
                                   |
                                   v
                           HISTORY / EVIDENCE
```

The Stream Health transition is detected once by Block 3.

The same transition object is then delivered independently to:

- Block 4 Event integration; and
- Block 5 Alarm Policy integration.

Block 5 does not redetect the transition.

## Production components

Block 5 introduces three Stream Health components.

### `StreamingHealthAlarmPolicy`

Location:

`app/services/streaming_health_alarm_policy.py`

Responsibility:

- receive an already-detected `StreamingHealthTransition`;
- determine alarm lifecycle intent;
- return an immutable `StreamingHealthAlarmDecision`.

Canonical actions are:

```text
NONE
RAISE
KEEP
RESOLVE
```

The initial production policy is intentionally conservative.

Health severity alone is not sufficient evidence to open an
operator-facing alarm.

Therefore, `DEGRADED`, `CRITICAL` or `UNKNOWN` Health does not
automatically authorize `RAISE`.

Richer policy inputs such as role, scope, operational impact,
expected presence and affected population belong to later blocks.

### `StreamingHealthTransitionAlarmFactory`

Location:

`app/services/streaming_health_transition_alarm_factory.py`

Responsibility:

- materialize an immutable `AlarmRecord`;
- only when policy explicitly returns `RAISE`.

The canonical alarm type introduced by Block 5 is:

```text
STREAM_HEALTH
```

Severity mapping for a policy-authorized alarm is:

```text
CRITICAL  -> CRITICAL
DEGRADED  -> MAJOR
other     -> WARNING
```

The factory does not:

- evaluate Stream Health;
- detect transitions;
- decide policy;
- persist alarms;
- manage alarm lifecycle.

### `StreamingHealthTransitionAlarmService`

Location:

`app/services/streaming_health_transition_alarm_service.py`

Responsibility:

- receive the already-detected Stream Health transition;
- evaluate the configured alarm policy exactly once;
- locate an existing active `STREAM_HEALTH` alarm;
- delegate lifecycle operations to the existing NOC `AlarmService`.

The service does not persist alarms directly and does not write
History/Evidence directly.

`AlarmService` remains the operational alarm lifecycle authority.

## Alarm lifecycle semantics

### NONE

No new alarm lifecycle operation is justified.

A Health transition may therefore produce an Event while producing no Alarm.

### RAISE

A new `STREAM_HEALTH` alarm may be materialized only when policy explicitly authorizes `RAISE`.

Before raising, the coordinator checks for an existing active `STREAM_HEALTH` alarm for the same node instance.

If one already exists, no equivalent duplicate alarm is created.

This includes an existing acknowledged alarm that still requires operational attention.

### KEEP

An existing alarm remains under its current lifecycle.

Partial Health improvement does not automatically resolve an existing alarm.

Likewise, transition to `UNKNOWN` after a problematic Health state does not automatically resolve the alarm.

### RESOLVE

A semantic recovery to `HEALTHY` may request resolution of an existing `STREAM_HEALTH` alarm.

Resolution is delegated to the existing `AlarmService`.

An acknowledged alarm can be resolved while preserving its acknowledgement metadata according to the existing NOC alarm lifecycle.

If no corresponding active alarm exists, recovery is a no-op for alarm lifecycle purposes.

## Conservative production policy

The current production policy deliberately does not emit `RAISE` solely from Stream Health severity.

This is required because the current Stream Health transition does not yet carry sufficient operational context to distinguish one optional reader degraded from a primary ingest unavailable or a service with many dependent readers affected.

Opening alarms from severity alone at this stage would violate the Stream Health contract and could create false operator alarms or alarm storms.

The `RAISE` action is nevertheless part of the Block 5 contract and its integration with the existing `AlarmService` is covered by controlled automated tests.

Production authorization criteria will evolve only when the required role, scope and impact context becomes available under later controlled blocks.

## Event and Alarm independence

Block 5 preserves the invariant: `Event != Alarm`.

An Event records that a semantic transition happened.

An Alarm represents a condition selected by policy as requiring operator attention.

Therefore, `DEGRADED` or `CRITICAL` Health may produce a semantic transition and a durable Event while the Alarm Policy legitimately returns `NONE`.

A `CRITICAL` Event is not itself authorization to open an Alarm.

## Dashboard integration

`DashboardApplication` computes the effective Stream Health and obtains one semantic Stream Health transition from the Block 3 transition detector.

That exact transition is passed to both `StreamingHealthTransitionEventService` and `StreamingHealthTransitionAlarmService`.

Automated integration validation verifies object identity between the transition delivered to both services.

This prevents duplicate transition detection and preserves one canonical operational fact.

## Runtime composition

`build_dashboard_application()` composes Block 5 using the existing NOC infrastructure.

`SQLiteHistoryDatabase` provides the existing alarm history repository, while `JsonlEvidenceWriter` provides the existing durable evidence projection.

`AlarmService` is constructed with the existing `NodeRegistry`, SQLite alarm history repository and JSONL evidence writer, and is then used by `StreamingHealthTransitionAlarmService`.

Block 5 therefore introduces no parallel alarm database, no parallel evidence format and no independent lifecycle authority.

## Automated validation

The Block 5 policy, factory and coordinator slice completed with `31 passed`.

The integrated Blocks 1-5 regression completed with `179 passed`. The final full-backend regression completed with `3158 passed`, `0 failed`, and `1` unrelated Starlette/httpx deprecation warning in `65.94 s`.

Additional validated slices include: Block 1 with 19 passed, Block 2 with 22 passed, Block 3 with 18 passed, Block 4 with 18 passed, Dashboard integration with 27 passed, existing NOC AlarmService with 37 passed, and Configuration with 7 passed.

Compilation completed without errors.

`git diff --check` completed without errors.

## Acceptance coverage

Automated validation covers the Block 5 policy boundary, explicit `RAISE` authorization, alarm deduplication, acknowledged-alarm preservation, recovery resolution, no-op recovery without an active alarm, Event and Alarm independence, reuse of the existing `AlarmService`, and delivery of the same semantic transition to both Event and Alarm integrations.

It also verifies that Health severity alone does not authorize alarm creation and that Block 5 does not introduce a second transition detector or a parallel alarm lifecycle.

## Physical validation - stable baseline

A physical observer was executed against the current operational MediaMTX environment using the Block 5 worktree.

Initial state: Stream Health `HEALTHY`, `STREAM_HEALTH` Events `9`, `STREAM_HEALTH` Alarms `0`, and `STREAM_HEALTH` Alarm transitions `0`.

The observer executed 180 cycles without an effective Stream Health transition.

Final durable state: Events `9 -> 9` with delta `0`; Alarms `0 -> 0` with delta `0`; Alarm transitions `0 -> 0` with delta `0`.

This validates the stable/no-flood baseline: stable Health does not invent semantic Events, does not create Stream Health alarms, and does not create spurious alarm lifecycle transitions.

The Block 5 runtime therefore executed against the physical environment for 180 observation cycles without Event or Alarm flooding.

## Physical validation - controlled real transition

A controlled physical validation was executed with the IMPACT SRT reader while the existing EJTV reader remained operational. No artificial network impairment was introduced. The physical environment produced real Stream Health degradation and recovery transitions from observed SRT session quality.

The durable baseline before the controlled sequence was `STREAM_HEALTH` Events `35`, Alarms `0`, and Alarm transitions `0`. During the validation, IMPACT was observed as `DEGRADED` while EJTV remained `HEALTHY` and Node Health remained `HEALTHY`. The production Alarm Policy did not create a `STREAM_HEALTH` alarm from severity alone.

SQLite recorded real sequences including `HEALTHY -> DEGRADED` at `2026-09-09T15:44:40.480626Z` followed by `DEGRADED -> HEALTHY` at `2026-09-09T15:44:43.086863Z`, and another degradation at `15:45:27.214250Z` followed by recovery at `15:45:32.404175Z`. The corresponding records were also projected to the daily JSONL evidence file.

Final durable state after the controlled sequence: Events `35 -> 40`, Alarms `0 -> 0`, and Alarm transitions `0 -> 0`. This validates the Block 5 production boundary: real Health transitions create durable NOC Events, while severity alone does not authorize Alarm creation. Recovery is recorded without inventing alarm lifecycle transitions.

## Block boundary

Block 5 does not implement service/client aggregation policy, role-aware alarm authorization, expected-presence semantics, affected-population policy, common-cause aggregation, additional protocol Health evaluators, video essence Health, audio essence Health, or ENG-014 Media Service Control Plane.

Those responsibilities remain outside this block.

## Current result

Block 5 status at this evidence point:

- INSPECTION: complete
- DESIGN / CONTRACT: complete
- TEST-FIRST: complete
- IMPLEMENTATION: complete
- DASHBOARD INTEGRATION: complete
- LIVE MONITOR COMPOSITION: complete
- INTEGRATED REGRESSION: complete
- PHYSICAL STABLE / NO-FLOOD BASELINE: complete
- PHYSICAL REAL TRANSITION: complete
- FINAL BLOCK CLOSURE: pending

Block 5 must not be declared closed until the final regression, documentation verification, commit, push and origin verification are complete.
