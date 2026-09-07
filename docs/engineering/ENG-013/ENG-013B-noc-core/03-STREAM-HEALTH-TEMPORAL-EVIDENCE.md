# ENG-013B - Stream Health Temporal Evidence

## Scope

Validation evidence for:

`Block 2 - TEMPORAL HEALTH`

The purpose of Block 2 is to prevent excessive sensitivity to individual
samples and unjustified Health flapping while preserving current telemetry.

This document does not define production timing values.

## Architecture validated

MediaMTX
-> MediaMTXSessionAdapter
-> SessionSnapshot
-> SessionQuality
-> StreamingHealthService
-> instantaneous Stream Health
-> SRTConnectionHealthStabilizer
-> StreamingHealthStabilizer
-> effective Stream Health

Temporal stabilization modifies effective Health status only.
Current telemetry remains current.

## Configuration

Temporal stabilization is optional and is enabled only when both variables
are configured:

STREAM_HEALTH_SRT_DEGRADATION_SECONDS
STREAM_HEALTH_SRT_RECOVERY_SECONDS

No production timing policy is defined by Block 2.

## Controlled temporal validation

Production stabilizer classes were exercised in memory using test-only
windows of 10 seconds for degradation and 10 seconds for recovery.

t=0   instant HEALTHY   effective HEALTHY
t=1   instant DEGRADED  effective HEALTHY
t=5   instant HEALTHY   effective HEALTHY
t=10  instant DEGRADED  effective HEALTHY
t=15  instant DEGRADED  effective HEALTHY
t=20  instant DEGRADED  effective DEGRADED
t=21  instant HEALTHY   effective DEGRADED
t=25  instant HEALTHY   effective DEGRADED
t=31  instant HEALTHY   effective HEALTHY

This demonstrates:

- temporary anomaly without unjustified flapping;
- persistence before committing degradation;
- hysteresis during recovery;
- stable recovery to HEALTHY.

At t=1 the effective status remained HEALTHY while current RTT was
120.0 ms.

This confirms the invariant:

stabilize status, not telemetry

## Physical SRT evidence

A real SRT connection associated with the IMPACT signal was observed on
MediaMTX.

The same connection showed intermittent packet-loss bursts mixed with
intervals containing no newly observed packet loss.

This demonstrated a real transport degradation rather than a synthetic
condition.

The inspection also showed that current SessionQuality loss and
retransmission percentages are derived from cumulative session counters.

Block 2 does not alter that Block 1 behavior and does not introduce a
parallel packet-loss evaluator.

## Automated validation

Targeted Block 2 regression:

51 passed

Related Stream Health, adapter and domain regression:

611 passed

Full backend regression:

3086 passed, 1 warning

The warning is an external Starlette/httpx deprecation warning and is not
a test failure.

git diff --check completed without errors.

## Acceptance coverage

Validated coverage includes:

- temporary anomaly;
- persistent degradation;
- persistent CRITICAL behavior through automated tests;
- persistent UNKNOWN behavior;
- stable recovery;
- independent temporal state per SRT connection;
- reset behavior;
- zero-duration configured windows;
- rejection of backward observation time;
- preservation of current telemetry.

## Boundary

Block 2 does not create or modify Events, Alarms, alarm policies, durable
History/Evidence lifecycle, additional protocol Health evaluators, or
multiprotocol aggregation policy.

## Result

ENG-013B Block 2 temporal stabilization satisfies the validated persistence,
hysteresis, anti-flapping and recovery requirements without establishing
arbitrary production timing thresholds.
