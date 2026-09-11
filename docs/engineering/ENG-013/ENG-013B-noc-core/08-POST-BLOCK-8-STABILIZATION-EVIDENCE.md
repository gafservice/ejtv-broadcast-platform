# ENG-013B — Post-Block-8 Stabilization Evidence

## 1. Scope

This document records the post-Block-8 stabilization and presentation
increments applied after the formal closure of RTMP Health.

The work remains inside ENG-013B and does not start ENG-014.

The increments covered are:

1. RTMP bitrate projection into CONNECTED CLIENTS.
2. RTMP temporal health stabilization window.
3. SRT health projection into CONNECTED CLIENTS.
4. ACTIVE CLIENTS outbound traffic consistency using specialized RTMP
   bitrate evidence.

No changes were introduced to MediaMTX, SRT health calculation,
RTMP raw health calculation, alarm policy, event policy, or the
multiprotocol aggregation contract.

---

## 2. RTMP bitrate projection

CONNECTED CLIENTS originally showed RTMP health correctly but bitrate as
N/A because the generic session measurement did not always provide a
usable RTMP bitrate.

The presentation layer was extended so that, when exactly one compatible
RTMPConnectionHealth evidence item exists for a session and
effective_bitrate_mbps is available, CONNECTED CLIENTS projects that
specialized bitrate.

If specialized RTMP bitrate is unavailable, the existing session bitrate
fallback is preserved.

Ambiguous specialized RTMP evidence is not selected arbitrarily.

The RTMP health calculation itself was not modified.

---

## 3. RTMP temporal stabilization

Physical observation showed an intermittent pattern:

- RTMP HEALTHY with valid bitrate.
- followed by RTMP UNKNOWN / N/A.
- followed again by RTMP HEALTHY.

A direct one-second diagnostic demonstrated that MediaMTX cumulative
counters can remain unchanged across adjacent dashboard sampling cycles
and then advance in bursts.

The raw RTMP health contract remains correct:

- positive monotonic effective delta -> HEALTHY;
- zero delta -> UNKNOWN;
- invalid/reset evidence -> UNKNOWN.

To avoid projecting brief counter-publication gaps as platform instability,
a presentation/aggregation stabilization layer was added:

RTMPConnectionHealthWindow(window_seconds=5.0)

The window is applied after raw RTMP health evaluation and before
aggregation and dashboard presentation.

Contract:

- first UNKNOWN remains UNKNOWN;
- HEALTHY is accepted immediately;
- HEALTHY refreshes the valid evidence timestamp;
- a brief UNKNOWN after recent HEALTHY preserves HEALTHY while age < 5 s;
- age >= 5 s returns UNKNOWN;
- observations moving backward in time are rejected;
- connections are independent;
- DEGRADED and CRITICAL are passed through;
- only status/message are stabilized;
- bitrate and delta are not frozen during held UNKNOWN.

Therefore a stabilized HEALTHY state may temporarily have:

effective_delta_bytes = None
effective_bitrate_mbps = None

This is intentional and avoids presenting stale traffic measurements.

---

## 4. SRT health projection into CONNECTED CLIENTS

CONNECTED CLIENTS was extended to project already-computed specialized
SRTConnectionHealth from StreamingHealth.

Matching uses session identity and path compatibility.

Contract:

- unique compatible SRT evidence -> project status;
- HEALTHY -> HEALTHY;
- DEGRADED -> DEGRADED;
- CRITICAL -> CRITICAL;
- UNKNOWN -> UNKNOWN;
- missing evidence -> N/A;
- ambiguous evidence -> N/A.

UNKNOWN specialized SRT evidence is valid evidence and is not replaced by
generic SessionQuality.

No new SRT health calculation was introduced in the dashboard.

---

## 5. ACTIVE CLIENTS traffic contract

Inspection confirmed the historical ACTIVE CLIENTS semantics:

- total_inbound_bitrate_mbps is the sum of session bitrate_receive_mbps;
- total_outbound_bitrate_mbps is the sum of session bitrate_send_mbps;
- the renderer labels outbound_bitrate_bps as "Total traffic";
- Avg/client is outbound_bitrate_bps / total_sessions.

Therefore this increment preserves "Total traffic" as outbound traffic
toward clients rather than redefining it as bidirectional traffic.

The presentation layer now enriches the outbound total for RTMP READER
sessions using specialized RTMP bitrate evidence.

Contract:

- start from SessionMeasurement.total_outbound_bitrate_mbps;
- SRT and other protocols preserve native measurement contribution;
- RTMP READER with exactly one compatible specialized evidence item and
  effective_bitrate_mbps available:
    - subtract its native bitrate_send_mbps contribution;
    - add the specialized RTMP bitrate;
- this is replacement, not double counting;
- RTMP READER with specialized bitrate None preserves the native value;
- ambiguous RTMP evidence preserves the native value;
- missing RTMP evidence preserves the native value;
- RTMP PUBLISHER specialized bitrate is not added to outbound traffic.

SessionService, SessionMeasurement and the ACTIVE CLIENTS renderer were not
redefined by this increment.

---

## 6. Automated verification

Final regression after the post-Block-8 increments:

- DashboardService: 63 passed
- Dashboard suite: 399 passed
- RTMPConnectionHealthWindow: 7 passed
- Full backend: 3301 passed
- Warnings: 1 known Starlette/httpx TestClient deprecation warning
- git diff --check: clean

The warning is pre-existing and unrelated to these changes.

The RTMP outbound presentation contract includes explicit tests for:

- specialized RTMP reader bitrate contribution;
- replacement instead of double counting;
- fallback when specialized bitrate is unavailable;
- fallback on ambiguous specialized evidence;
- RTMP publisher not contributing specialized inbound bitrate to outbound.

The SRT presentation contract includes explicit tests for:

- HEALTHY projection;
- UNKNOWN preservation;
- ambiguous evidence rejection.

---

## 7. Physical validation

Physical validation was performed on ejtv-01 with MediaMTX and the live
dashboard running against real traffic.

Observed CONNECTED CLIENTS:

- ejtv:
  - protocol: SRT
  - role: READER
  - health: HEALTHY
  - bitrate approximately 4.19 Mbps

- impact:
  - protocol: RTMP
  - role: READER
  - health: HEALTHY
  - bitrate approximately 5.44 Mbps

Observed ACTIVE CLIENTS:

- SRT: 1
- RTMP: 1
- TOTAL: 2
- Total traffic: approximately 10.03 Mbps
- Avg/client: approximately 5.02 Mbps

The displayed total is consistent with the presence of both SRT and RTMP
reader traffic and no longer reflects only the native SRT contribution.

Exact instantaneous values are expected to vary because the generic
MediaMTX session counters and the specialized RTMP temporal observation
do not necessarily update on exactly the same sampling instant.

Observed PLATFORM HEALTH:

- Status: HEALTHY
- Worst: HEALTHY
- Services: 2
- Coverage: 100%
- Affected: 0%
- H: 2
- D: 0
- C: 0
- U: 0

Observed ACTIVE ALARMS:

- 0

The result confirms that the presentation corrections did not regress
multiprotocol platform health.

---

## 8. Architectural result

The resulting flow is:

SessionSnapshot
    -> raw RTMP health
    -> RTMP temporal stabilization
    -> multiprotocol aggregation
    -> dashboard presentation

For presentation:

SessionMeasurement
    + stabilized StreamingHealth
    + stabilized RTMPConnectionHealth
    -> ACTIVE CLIENTS
    -> CONNECTED CLIENTS

The generic measurement layer remains protocol-independent while
specialized protocol evidence is introduced only where needed for
health and presentation enrichment.

---

## 9. Closure status

Post-Block-8 stabilization:

- RTMP bitrate presentation: GREEN
- RTMP temporal health window: GREEN
- SRT health projection: GREEN
- ACTIVE CLIENTS RTMP outbound consistency: GREEN
- automated regression: GREEN
- physical validation: GREEN

ENG-013B remains active.

ENG-014 has not started.
