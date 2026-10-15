# ENG-013C — INCOMING V2
## Visual Presentation Contract

**Block:** 235E.28B.1
**Project:** Enlace Broadcast Platform (EBP)
**Component:** NOC / INCOMING Dashboard
**Status:** CONTRACT REVIEWED — Ready for RED tests
**Reference:** User-approved INCOMING visual prototype

---

## V2-01 — Purpose

Define the visual presentation of the INCOMING Dashboard
using Rich terminal components.

The implementation must approximate the approved visual
prototype while preserving existing operational behavior.

This contract governs presentation only.

---

## V2-02 — Scope

Included:

- Compact incoming signal list.
- Selected signal header.
- Six contextual navigation tabs.
- Four technical information cards for SIGNAL.
- Adaptive terminal presentation.
- Existing canonical signal selection.
- Existing operational data and formatting.

Excluded:

- New telemetry capture.
- New Health evaluation.
- Alarm policy modifications.
- Transport protocol changes.
- Changes to the ENG-013A domain contract.
- Web interface implementation.

---

## V2-03 — Visual Structure

The normal INCOMING view consists of:

1. Terminal header.
2. Incoming signal list.
3. Selected signal header.
4. Contextual tab navigation.
5. Detail content.

The selected signal detail must not depend on the number
of incoming signals being exactly three.

---

## V2-04 — Incoming Signal List

The signal list must:

- Use canonical IncomingPanelData.
- Preserve the selected path_name.
- Support additional incoming signals.
- Preserve viewport navigation and scrolling.
- Preserve operational status, Health and alarm indicators.
- Adapt its columns to terminal width.
- Avoid unnecessary vertical whitespace where feasible.

The final height policy must be validated against existing
viewport and terminal geometry contracts.

---

## V2-05 — Selected Signal Header

The selected signal header identifies:

- Canonical path_name.
- Operational status, when available.
- Canonical Health status, when available.

Missing values must be represented as unavailable.

The renderer must not infer Health or operational state.

---

## V2-06 — Contextual Tabs

The six tabs are:

1. SIGNAL
2. TRANSPORT
3. VIDEO
4. AUDIO
5. EVENTS
6. STATISTICS

The active tab must be visually distinguishable.

The tab strip must appear above the detail content
in the normal V2 presentation.

Keyboard navigation remains restricted to INCOMING.

Changing tabs must preserve the selected signal.

---

## V2-07 — SIGNAL Cards

The SIGNAL tab contains four visual sections:

### Identification

- Path
- Source
- Protocol
- Remote address / origin

### Reception

- Operational status
- Receive bitrate
- Reception since: N/A until a canonical reception-start
  projection is available.
- Reception duration: N/A until a canonical reception-duration
  projection is available.

Health timestamps must never be presented as reception timestamps.

### Health

- Canonical Health status
- Health reason
- Health since
- Health duration

### Alarms

- Canonical alarm count
- Canonical alarm severity
- Existing alarm summary

Fields must originate from existing IncomingPanelData
and IncomingRowData projections.

The presentation layer must not invent missing data.

---

## V2-08 — Specialized Tabs

TRANSPORT, VIDEO, AUDIO, EVENTS and STATISTICS
must remain navigable.

Until specialized projections are implemented,
their unavailable metrics must remain explicitly N/A.

No synthetic telemetry may be introduced.

---

## V2-09 — Adaptive Presentation

Existing presentation thresholds are:

- Compact: terminal width below 100 columns.
- Operational: 100 through 139 columns.
- Full: 140 columns and above.

These thresholds are the current baseline.

Any changes require separate tests and justification.

Full and operational modes target a two-column,
four-card presentation where geometry permits.

Compact mode prioritizes:

- Selected signal identity.
- Health.
- Alarms.
- Receive bitrate.
- Protocol.

At insufficient terminal heights, preserve the existing
notice and avoid hiding critical operational information.

---

## V2-10 — Geometry and Visibility

The layout must:

- Preserve access to all incoming signals.
- Avoid clipping critical fields where supported by
  the existing compact contracts.
- Adapt to terminal width and height.
- Avoid excessive blank space.
- Keep the active tab identifiable.
- Preserve existing navigation and viewport behavior.

The geometry policy must be tested independently
before replacing the existing layout.

Operational visibility takes priority over four-card symmetry.

When terminal geometry is insufficient, the presentation
must degrade gracefully to a compact layout while preserving
critical signal identity, Health, alarms, bitrate and protocol.

No minimum geometry for four-card presentation is approved
until supported by explicit rendering tests.

---

## V2-11 — Data Integrity

Renderers may format existing values.

Renderers must not:

- Recalculate canonical Health.
- Generate alarm decisions.
- Fabricate bitrate, timestamps or event data.
- Modify the selected signal.
- Mutate domain or application state.

Unavailable values must remain distinguishable
from valid zero values.

---

## V2-12 — Compatibility

The existing SIGNAL DETAIL implementation
must remain available during incremental migration.

The six-tab navigation contract remains unchanged.

Existing dashboard tests form the regression baseline:

793 passed at block 235E.27E.4.

New visual behavior requires additional tests.

---

## V2-13 — Implementation Strategy

Development sequence:

1. Inspect and define geometry.
2. Add visual contract tests (RED).
3. Implement selected signal header.
4. Implement tab navigation placement.
5. Implement SIGNAL card renderer.
6. Integrate adaptive layout.
7. Run focused and full regression.
8. Perform physical terminal acceptance.
9. Review changes and stage selectively.
10. Commit and push only after approval.

Each step must remain independently verifiable.

---

## V2-14 — Acceptance Criteria

Acceptance requires:

- Visual structure consistent with approved prototype.
- Compact incoming list.
- Selected signal header.
- Tabs above detail content.
- Four SIGNAL information cards when space permits.
- Correct real operational data.
- Correct unavailable-value presentation.
- Preservation of selection and navigation.
- Compatibility with future incoming signals.
- No Health or alarm policy regression.
- Passing focused and full dashboard tests.
- Physical verification on ejtv-01.

---

## V2-15 — Change Control

This document is a proposed presentation contract.

No production modification is authorized merely
by creating this document.

Any implementation change must follow:

INSPECTION
-> CONTRACT
-> TEST RED
-> MINIMAL PRODUCT
-> GREEN
-> REGRESSION
-> PHYSICAL ACCEPTANCE
-> REVIEW
-> COMMIT
-> PUSH

---

## V2-16 — Open Technical Decisions

The following remain subject to inspection and testing:

- Exact incoming list height calculation.
- Exact minimum terminal height for four cards.
- Card dimensions and overflow behavior.
- Rich layout nesting strategy.
- Terminal header styling.
- Behavior at extreme terminal dimensions.

These decisions must not be implemented by assumption.

---

## V2-17 — Evidence

Baseline:

- ENG-013C / 235E.27E.4
- 793 dashboard tests passed.
- Python syntax validation passed.
- git diff --check passed.

Architecture inspection:

- ENG-013C / 235E.28A.1

Geometry and presentation inspection:

- ENG-013C / 235E.28A.2

Visual reference:

- User-approved INCOMING dashboard prototype.

No commit or push performed for this contract.
