# ENG-013C — INCOMING Signal Detail Contract

## 1. Purpose

This contract defines the first contextual Signal Detail presentation
for the EBP terminal dashboard INCOMING view.

Signal Detail presents information about the currently selected
incoming signal.

It does not introduce a new observation, Health evaluation,
alarm policy, or independent monitoring subsystem.

## 2. Architectural boundary

The presentation flow is:

    NOC operational state
        |
        v
    Dashboard application/service
        |
        v
    IncomingPanelData
        |
        +-- IncomingRowData
        |
        +-- IncomingSelectionState
        |
        v
    Signal Detail presentation

The existing NOC domain/application state remains authoritative.

Signal Detail must not independently evaluate Media Health,
Transport Health, Signal Health, or alarm severity.

## 3. Scope

The first Signal Detail implementation covers:

- selected signal identification;
- source and protocol information;
- remote endpoint information;
- reception status and bitrate;
- canonical Health status;
- canonical Health reason;
- canonical Health since;
- existing alarm count;
- existing maximum alarm severity.

All information must originate from the current dashboard
presentation snapshot.

## 4. Explicitly outside scope

This contract does not introduce:

- additional media capture;
- new MediaMTX queries;
- new backend polling;
- independent Health calculations;
- new Health thresholds;
- independent alarm evaluation;
- historical charts;
- transport-specific advanced metrics;
- video/audio technical analysis;
- new terminal operational views;
- new keyboard navigation actions.

These capabilities belong to existing or subsequent
engineering blocks.

## 5. Selection identity

SD-01:

Signal Detail must reuse the existing IncomingSelectionState.

SD-02:

The selected signal is identified by selected_path_name,
which corresponds to IncomingRowData.path_name.

Selection must be resolved by exact path_name equality.

The renderer must not introduce an independent selection state.

## 6. Data source

SD-03:

Signal Detail must not trigger additional captures.

SD-04:

Signal Detail must consume only information already projected
into the current IncomingPanelData.

The detail must not combine unrelated capture generations.

The first implementation must not require changes to the
existing domain observation contracts.

## 7. Health boundary

SD-05:

Signal Detail must present the existing canonical Health values.

It must not calculate, reinterpret, stabilize, or override Health.

Missing Health evidence must not be interpreted as unhealthy.

## 8. Alarm boundary

SD-06:

Signal Detail must present existing alarm projections.

It must not calculate alarm count, infer severity,
or create alarm transitions.

Alarm information must remain consistent with the existing
INCOMING row projection.

## 9. Selection consistency

SD-07:

If selected_path_name does not match a row in the current
IncomingPanelData, Signal Detail must not display information
from another signal.

SD-08:

When no valid selected signal exists, Signal Detail must
present an explicit empty or unavailable selection state.

Selection reconciliation remains the responsibility of
DashboardApplication.

## 10. Renderer compatibility

SD-09:

Existing IncomingPanelRenderer behavior must remain compatible.

The INCOMING table must preserve its existing columns,
selection highlighting, and supported legacy render calls.

Signal Detail must not mutate IncomingPanelData or IncomingRowData.

## 11. Terminal navigation

SD-10:

The six existing operational views remain unchanged:

- GENERAL
- INCOMING
- OUTGOING
- SYSTEM
- ALARMS
- EVENTS

Signal Detail is a contextual panel within INCOMING.

It is displayed below the existing incoming signal list.

UP and DOWN continue changing the selected incoming signal.

HOME and END retain their existing selection behavior.

LEFT and RIGHT retain their existing view-navigation behavior.

No OPEN_DETAIL or BACK action is introduced.

## 12. Domain compatibility

SD-11:

ENG-013A frozen contracts remain unchanged.

Existing ENG-013B Health, events, alarms, history,
and evidence mechanisms remain authoritative.

The presentation layer must not duplicate them.

## 13. Future extensibility

SD-12:

The implementation must allow subsequent presentation
specializations without requiring a second selection identity.

Future blocks may add:

- Transport Detail;
- Video/Audio Detail;
- Events/Alarms/History;
- Trends/Statistics.

Those capabilities are not implemented by this contract.

## 14. Presentation behavior

The contextual detail panel must be displayed below
the existing INCOMING signal list.

The panel must update when:

- the selected path changes;
- the current dashboard snapshot changes.

The first implementation must present the following categories:

### Identification

- Path
- Source

### Transport

- Protocol
- Remote endpoint

### Reception

- Status
- Receive bitrate

### Health

- Health status
- Health reason
- Health since

### Alarms

- Active alarm count
- Maximum alarm severity

Missing optional values must be presented explicitly,
using N/A or an equivalent established unavailable marker.

A missing alarm severity must not be interpreted as
an independently evaluated alarm state.

## 15. Layout constraints

The existing INCOMING signal list must remain visible.

Signal Detail must occupy a separate contextual region
below the list.

The implementation must preserve practical readability
and must not silently remove existing INCOMING columns.

Terminal-height constraints must be verified through
renderer tests and physical acceptance.

This contract does not prescribe fixed terminal dimensions
or arbitrary layout proportions before implementation evidence.

## 16. Acceptance conditions

The implementation is ready for acceptance when:

1. Signal Detail uses IncomingSelectionState.
2. The selected row is resolved by path_name.
3. No additional capture is triggered.
4. Only current IncomingPanelData is consumed.
5. Health values are presented without recalculation.
6. Alarm values are presented without recalculation.
7. Invalid selection never displays another signal.
8. Empty selection produces an explicit empty state.
9. Existing INCOMING renderer behavior remains compatible.
10. All six operational views remain unchanged.
11. ENG-013A and ENG-013B contracts remain unchanged.
12. The panel supports future specialization.
13. Selection changes update the displayed detail.
14. Snapshot changes update the displayed detail.
15. Missing optional values are presented safely.
16. INCOMING list and Signal Detail coexist in the layout.
17. Targeted tests and regression tests pass.
18. Physical terminal acceptance is recorded separately.

## 17. Engineering workflow

Implementation must follow:

    CONTRACT
       |
       v
    TEST RED
       |
       v
    MINIMAL PRODUCT CHANGE
       |
       v
    GREEN
       |
       v
    REGRESSION
       |
       v
    PHYSICAL ACCEPTANCE
       |
       v
    COMMIT
       |
       v
    PUSH
       |
       v
    REMOTE VERIFICATION

No production implementation should precede
contract acceptance and the corresponding RED tests.

## 18. Contract status

Engineering block: ENG-013C / 235E.26

Contract: INCOMING Signal Detail

Functional requirements: SD-01 through SD-12

Functional design: approved

Implementation: not started

Targeted RED tests: not started

Physical acceptance: pending

This document records the approved functional design.
It does not constitute evidence of implementation,
test success, or physical acceptance.
