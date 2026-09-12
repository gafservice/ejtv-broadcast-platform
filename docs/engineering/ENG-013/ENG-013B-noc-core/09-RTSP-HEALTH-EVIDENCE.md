# ENG-013B — RTSP Health Evidence

## 1. Scope

This document records the implementation and validation of specialized
RTSP Health inside ENG-013B.

The work extends the existing multiprotocol health architecture after
the formal RTMP Health and post-Block-8 stabilization increments.

The increment covers:

1. specialized RTSP session health domain;
2. temporal RTSP health evaluation;
3. multiprotocol aggregation;
4. DashboardApplication runtime integration;
5. dashboard snapshot transport;
6. RTSP health and bitrate projection into CONNECTED CLIENTS;
7. RTSP outbound traffic enrichment in ACTIVE CLIENTS;
8. automated regression;
9. physical validation against real MediaMTX RTSP sessions.

The work remains inside ENG-013B.

ENG-014 has not started.

HLS Health is not implemented by this increment.

---

## 2. Physical RTSP model

Inspection of MediaMTX confirmed that RTSP exposes both connection and
session resources.

The specialized v1 health entity is the RTSP session rather than the
RTSP control connection.

The authoritative MediaMTX resource used by the existing session adapter
is:

    /v3/rtspsessions/list

Physical validation confirmed that an RTSP session exposes evidence such
as:

- session id;
- path;
- state;
- transport;
- profile;
- connection references;
- bytes received;
- bytes sent;
- RTP packet counters;
- RTCP packet counters.

The existing normalized ActiveSession model already provides the identity,
role, path and byte-counter evidence required for the v1 transport-health
contract.

Therefore v1 does not introduce a parallel RTSP observation model.

RTSP connection resources remain secondary transport/control evidence and
are not used as the authoritative v1 health population.

Transport, profile and RTP/RTCP statistics remain available as future
evidence but are not interpreted as RTSP Health thresholds in this
increment.

---

## 3. RTSPSessionHealth domain

The specialized domain model is:

    RTSPSessionHealth

Its fields are:

- session_id;
- path_name;
- state;
- effective_delta_bytes;
- effective_bitrate_mbps;
- status;
- message.

The model intentionally does not include RTMP-specific evidence such as
outbound frame discard counters.

It also does not introduce transport/profile/RTP health semantics that are
not yet represented consistently by the normalized session domain.

The canonical HealthStatus values remain:

- HEALTHY;
- DEGRADED;
- CRITICAL;
- UNKNOWN.

DEGRADED and CRITICAL remain valid domain states but are not fabricated
without explicit RTSP evidence and policy.

---

## 4. Temporal RTSP Health contract

RTSPSessionHealthService evaluates consecutive SessionSnapshot
observations.

Temporal compatibility requires:

- identical session_id;
- protocol RTSP;
- compatible path;
- compatible role;
- compatible connected_since.

Direction is determined by SessionRole:

- READER -> bytes_sent;
- PUBLISHER -> bytes_received;
- UNKNOWN -> insufficient directional evidence.

The effective delta is:

    current effective counter - previous effective counter

The effective bitrate is:

    delta_bytes * 8 / interval_seconds / 1_000_000

Contract:

- first observation -> UNKNOWN;
- non-positive observation interval -> UNKNOWN;
- unknown role -> UNKNOWN;
- negative/reset counter delta -> UNKNOWN;
- zero delta -> UNKNOWN;
- positive monotonic delta -> HEALTHY;
- path=None does not produce specialized RTSP health;
- non-RTSP sessions do not produce specialized RTSP health;
- session disappearance does not fabricate a CRITICAL ghost session.

The contract is observed-only.

Expected Presence remains a separate higher-level concern.

---

## 5. No RTSP stabilization window required

A dedicated one-second physical diagnostic was performed against a real
RTSP reader.

After the expected first UNKNOWN observation, fourteen consecutive
one-second observations produced positive byte deltas and HEALTHY status.

Observed specialized RTSP bitrate varied approximately between 5.17 Mbps
and 7.54 Mbps for the controlled impact reader.

This differs from the previously observed RTMP counter-publication
behavior, where adjacent one-second samples can contain unchanged
cumulative counters followed by burst updates.

No equivalent RTSP zero-delta oscillation was observed.

Therefore no RTSP temporal stabilization window was introduced.

The raw temporal contract remains authoritative.

A stabilization layer should only be introduced later if physical
evidence demonstrates a real need.

---

## 6. Multiprotocol aggregation

StreamingHealthAggregator accepts specialized RTSP session health
evidence in addition to the existing SRT and RTMP evidence.

The population authority remains SessionSnapshot.

Specialized RTSP evidence cannot create ghost sessions.

Matching uses:

- RTSP session identity;
- compatible path;
- exactly one specialized evidence item.

Contract:

- exactly one compatible specialized RTSP health item -> use its status;
- specialized UNKNOWN remains UNKNOWN;
- missing specialized evidence -> generic SessionQuality fallback;
- ambiguous specialized evidence -> generic SessionQuality fallback;
- incompatible path -> generic SessionQuality fallback;
- orphan specialized evidence -> ignored.

The temporal service owns the stricter continuity checks.

Aggregation does not independently reconstruct temporal identity.

---

## 7. Dashboard runtime integration

DashboardApplication owns the previous SessionSnapshot already required by
temporal protocol evaluation.

RTSPSessionHealthService is injected by the live monitor construction
path.

For each dashboard cycle:

    previous SessionSnapshot
        + current SessionSnapshot
        -> RTSPSessionHealthService
        -> specialized RTSP session health
        -> StreamingHealthAggregator
        -> PlatformHealth
        -> DashboardSnapshotInput
        -> DashboardService

The first valid observation is therefore UNKNOWN.

Subsequent compatible observations with positive effective traffic become
HEALTHY.

The previous SessionSnapshot is updated only through the normal successful
dashboard build lifecycle.

---

## 8. CONNECTED CLIENTS projection

CONNECTED CLIENTS projects specialized RTSP evidence using session id and
path.

Contract:

- exactly one compatible RTSPSessionHealth -> project specialized status;
- HEALTHY -> HEALTHY;
- UNKNOWN -> UNKNOWN;
- specialized bitrate available -> project effective_bitrate_mbps;
- specialized bitrate unavailable -> preserve native session bitrate
  fallback;
- missing specialized evidence -> health N/A and native bitrate fallback;
- ambiguous specialized evidence -> health N/A and native bitrate fallback.

Specialized UNKNOWN is valid evidence and is not replaced by generic
SessionQuality.

No RTSP health calculation is performed inside the presentation layer.

---

## 9. ACTIVE CLIENTS outbound traffic contract

Inspection confirmed the existing ACTIVE CLIENTS semantics:

- SessionMeasurement.total_outbound_bitrate_mbps is based on native
  session bitrate_send_mbps;
- the dashboard presents this as Total traffic;
- Avg/client is Total traffic divided by total_sessions.

Physical inspection showed that RTSP readers can have:

    bitrate_send_mbps = None

while specialized temporal RTSP evidence provides a valid effective
bitrate.

The presentation layer therefore enriches outbound traffic using
specialized RTSP evidence.

For an RTSP READER with exactly one compatible specialized health item and
an available effective_bitrate_mbps:

    corrected_outbound
        =
    current_outbound
        - native_rtsp_send
        + specialized_rtsp_bitrate

This is replacement rather than addition.

Contract:

- RTSP READER + unique specialized bitrate -> replace native contribution;
- native bitrate missing -> native contribution is treated as zero;
- specialized bitrate None -> preserve native contribution;
- ambiguous specialized evidence -> preserve native contribution;
- missing specialized evidence -> preserve native contribution;
- RTSP PUBLISHER specialized receive bitrate is not added to outbound
  client traffic.

This preserves the existing RTMP replacement semantics and prevents double
counting if native RTSP bitrate becomes available in the future.

SessionService and SessionMeasurement remain protocol-independent.

---

## 10. Physical validation — RTSP transport

Physical validation was performed on ejtv-01 against MediaMTX v1.19.2.

A controlled RTSP reader was created against:

    rtsp://127.0.0.1:8554/impact

using FFmpeg with TCP transport and stream copy.

The physical session successfully entered MediaMTX as:

- state: read;
- path: impact;
- transport: TCP;
- profile: AVP;
- tracks: AAC + H.264.

Session-specific bytesSent advanced continuously.

A five-second observation produced approximately 5.62 Mbps from the
session-specific byte delta.

The controlled FFmpeg process was intentionally terminated by timeout.

Exit status 124 therefore represented the planned test termination rather
than an RTSP failure.

---

## 11. Physical validation — simultaneous RTSP sessions

During validation an independent real RTSP session was already active:

- path: enlace;
- role: reader;
- client: VLC;
- transport: TCP;
- profile: AVP.

The controlled impact reader was added without disturbing the existing
enlace session.

DashboardApplication observed both RTSP sessions simultaneously.

The first temporal cycle projected UNKNOWN, as required by the contract.

Subsequent cycles projected both RTSP sessions as HEALTHY.

Platform Health moved from the initial population containing UNKNOWN RTSP
observations to full specialized healthy coverage once temporal evidence
became available.

The existing enlace session remained active after the controlled impact
reader terminated.

---

## 12. Physical validation — CONNECTED CLIENTS

End-to-end physical validation confirmed specialized RTSP presentation
through the complete application and snapshot path.

Observed behavior:

- first temporal cycle:
  - RTSP health: UNKNOWN;
  - RTSP specialized bitrate: unavailable;

- subsequent cycles:
  - RTSP health: HEALTHY;
  - RTSP specialized bitrate: available.

For the real enlace RTSP reader, observed specialized bitrate was
approximately 4.19 to 4.62 Mbps during the final ACTIVE CLIENTS
validation.

The result confirms:

    MediaMTX
        -> SessionSnapshot
        -> RTSPSessionHealthService
        -> DashboardApplication
        -> DashboardSnapshotInput
        -> DashboardService
        -> CONNECTED CLIENTS

---

## 13. Physical validation — ACTIVE CLIENTS

The final physical validation observed three simultaneous reader sessions:

- ejtv / SRT;
- enlace / RTSP;
- impact / RTMP.

The generic SessionMeasurement contained native outbound bitrate only for
the SRT reader during this observation.

Example first stabilized cycle:

    Native SRT outbound       = 4.279 Mbps
    Native RTSP outbound      = None
    Native RTMP outbound      = None

Specialized dashboard presentation:

    SRT ejtv                  = 4.279 Mbps
    RTSP enlace               = 4.572 Mbps
    RTMP impact               = 3.824 Mbps
    ACTIVE CLIENTS traffic    = 12.675 Mbps
    Avg/client                = 4.225 Mbps
    Visible row bitrate sum   = 12.675 Mbps

Platform Health:

    HEALTHY
    H=3 D=0 C=0 U=0

The behavior remained coherent across the complete ten-cycle observation.

Additional examples:

    cycle 03:
        ACTIVE CLIENTS        = 14.217 Mbps
        visible row sum       = 14.217 Mbps

    cycle 06:
        ACTIVE CLIENTS        = 12.965 Mbps
        visible row sum       = 12.965 Mbps

    cycle 09:
        ACTIVE CLIENTS        = 12.391 Mbps
        visible row sum       = 12.391 Mbps

This physically confirms that specialized RTSP and RTMP evidence enrich
the presentation layer without redefining the generic SessionMeasurement.

---

## 14. Automated verification

Final RTSP regression:

- RTSP domain: 10 passed;
- RTSP temporal service: 10 passed;
- StreamingHealth aggregation: 79 passed;
- Dashboard suite: 409 passed;
- specialized health regression: 150 passed;
- full backend: 3336 passed;
- warnings: 1 known Starlette/httpx TestClient deprecation warning;
- py_compile: clean;
- git diff --check: clean.

The warning is pre-existing and unrelated to RTSP Health.

Explicit automated contracts include:

- RTSP domain validation;
- temporal first-observation UNKNOWN;
- reader and publisher direction;
- zero-delta UNKNOWN;
- counter reset handling;
- invalid interval handling;
- temporal identity compatibility;
- unknown role handling;
- non-RTSP rejection;
- pathless-session rejection;
- specialized aggregation precedence;
- specialized UNKNOWN preservation;
- missing/incompatible/ambiguous aggregation fallback;
- orphan evidence rejection;
- DashboardApplication temporal transport;
- CONNECTED CLIENTS specialized health;
- CONNECTED CLIENTS specialized bitrate;
- CONNECTED CLIENTS ambiguity behavior;
- ACTIVE CLIENTS RTSP specialized outbound contribution;
- replacement instead of double counting;
- native fallback when specialized bitrate is unavailable;
- native fallback on ambiguous evidence;
- RTSP publisher exclusion from outbound client traffic.

---

## 15. Architectural result

The resulting protocol-health flow is:

    SessionSnapshot
        -> RTSPSessionHealthService
        -> RTSPSessionHealth
        -> StreamingHealthAggregator
        -> PlatformHealth
        -> DashboardSnapshotInput
        -> DashboardService

Presentation combines:

    SessionMeasurement
        + specialized RTSP Health
        + stabilized RTMP Health
        + specialized SRT Health
        -> ACTIVE CLIENTS
        -> CONNECTED CLIENTS

The generic session measurement remains protocol-independent.

Specialized protocol evidence is introduced only where protocol-specific
health or presentation semantics require it.

The implementation preserves the architectural separation between:

- observed transport health;
- Expected Presence;
- Media/Track Health;
- Events;
- Alarms;
- durable History/Evidence.

RTSP absence is not fabricated as CRITICAL.

Expected service disappearance remains a future Expected Presence concern.

Track completeness, codec compatibility and RTP/media-quality semantics
remain future Media/Track Health concerns.

---

## 16. Closure status

RTSP Health specialization:

- domain contract: GREEN;
- temporal evaluation: GREEN;
- multiprotocol aggregation: GREEN;
- DashboardApplication integration: GREEN;
- Platform Health integration: GREEN;
- CONNECTED CLIENTS health: GREEN;
- CONNECTED CLIENTS bitrate: GREEN;
- ACTIVE CLIENTS outbound consistency: GREEN;
- automated regression: GREEN;
- physical validation: GREEN;
- RTSP stabilization window: not required by current physical evidence.

RTSP Health is functionally complete for the current ENG-013B scope.

ENG-013B remains active.

ENG-014 has not started.

The next protocol specialization planned inside ENG-013B is HLS Health.
