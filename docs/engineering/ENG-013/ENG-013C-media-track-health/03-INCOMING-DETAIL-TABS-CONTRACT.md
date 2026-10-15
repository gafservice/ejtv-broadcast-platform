# ENG-013C — INCOMING Detail Tabs Contract

## 1. Purpose

Define the structural navigation and presentation contract
for six contextual detail tabs within the EBP INCOMING dashboard.

The initial objective is to complete the dashboard structure
before implementing the full technical content of each tab.

## 2. Architectural boundary

The existing NOC operational state remains authoritative.

The presentation flow is:

    NOC operational state
        |
        v
    Dashboard application/service
        |
        v
    IncomingPanelData
        |
        +-- IncomingSelectionState
        |
        +-- IncomingDetailTabState
        |
        v
    DashboardRenderer
        |
        +-- IncomingPanelRenderer
        |
        +-- Contextual detail presentation

No additional observation or Health evaluation is introduced.

## 3. Detail tabs

IDT-01:

The INCOMING detail area must support exactly six tabs:

1. SIGNAL
2. TRANSPORT
3. VIDEO
4. AUDIO
5. EVENTS
6. STATISTICS

The default active tab is SIGNAL.

These are contextual tabs, not new TerminalView values.

## 4. Selection identity

IDT-02:

All tabs must reuse IncomingSelectionState.

The selected signal is identified by selected_path_name.

No tab may maintain an independent signal selection.

IDT-03:

Changing the active tab must not change selected_path_name.

Changing the selected signal must preserve the active tab,
provided the selected signal remains valid.

## 5. Navigation

IDT-04:

Within TerminalView.INCOMING, keys 1 through 6 select
the corresponding detail tab.

Outside INCOMING, these keys must not change the detail tab.

IDT-05:

Existing navigation behavior must remain compatible.

UP and DOWN retain incoming signal selection.

HOME and END retain incoming selection behavior.

LEFT and RIGHT retain terminal view navigation.

TAB and SHIFT+TAB retain their existing navigation behavior.

Q retains its existing quit behavior.

No existing key binding may be repurposed.

## 6. Data source

IDT-06:

All detail tabs must consume the current dashboard
presentation snapshot.

No tab may trigger additional capture, backend polling,
MediaMTX queries, or independent observation.

No tab may combine unrelated capture generations.

## 7. Initial content

IDT-07:

SIGNAL must preserve its existing contextual information.

TRANSPORT, VIDEO, AUDIO, EVENTS, and STATISTICS
may initially provide structural placeholders.

Missing metrics must be presented as unavailable.

No fabricated telemetry is permitted.

## 8. Health and alarms

IDT-08:

Detail tabs must not independently evaluate Health.

Canonical Health and alarm information remains authoritative.

No new Health thresholds, stabilization rules,
alarm transitions, or severity calculations are introduced.

## 9. Adaptive presentation

IDT-09:

The incoming signal list must remain visible whenever
terminal dimensions permit.

The selected signal must remain identifiable.

The active detail tab must remain identifiable.

The tab navigation must adapt to narrow terminals.

The detail content must adapt to limited vertical space.

No fixed layout assumption may break existing
compact, operational, or full presentation modes.

## 10. Signal compatibility

IDT-10:

The existing SignalDetailRenderer behavior must remain
compatible with its current contract and tests.

The new tab structure must not mutate IncomingPanelData
or IncomingRowData.

## 11. Missing selection

IDT-11:

If no valid selected signal exists, detail tabs must
present an explicit unavailable selection state.

No tab may display data from another signal.

## 12. Domain isolation

IDT-12:

ENG-013A frozen contracts remain unchanged.

Existing ENG-013B and ENG-013C Health, events,
alarms, history, and evidence mechanisms remain authoritative.

This block does not modify capture, transport,
media processing, or operational Health evaluation.

## 13. Acceptance criteria

The structural implementation is accepted when:

- all six tabs are reachable;
- SIGNAL remains the default tab;
- signal selection and tab selection remain independent;
- existing keyboard navigation remains compatible;
- changing tabs does not change canonical telemetry;
- missing metrics are not fabricated;
- compact terminal presentation remains usable;
- existing SIGNAL DETAIL tests remain GREEN;
- dashboard regression tests remain GREEN;
- physical navigation matches the approved visual prototype.

## 14. Implementation sequence

1. Contract approval.
2. RED tests.
3. Minimal structural implementation.
4. GREEN tests.
5. Dashboard regression.
6. Physical visual acceptance.
7. Selective commit.
8. Push and remote verification.

## 15. Explicitly outside scope

This structural block does not implement:

- advanced SRT or UDP metrics;
- video technical analysis;
- audio technical analysis;
- historical statistics;
- new alarm evaluation;
- additional backend services;
- new operational terminal views;
- independent telemetry capture.

Those capabilities belong to subsequent engineering blocks.
