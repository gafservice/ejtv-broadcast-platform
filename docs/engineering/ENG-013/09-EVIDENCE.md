# ENG-013 — Evidence Index

Este documento sirve como índice global de evidencia técnica para ENG-013.

La evidencia detallada de ENG-013B — NOC Core se mantiene en:

`docs/engineering/ENG-013/ENG-013B-noc-core/`

## ENG-013B — NOC Core

### Block 1 / Node Health Failure-Recovery

Documento:
`ENG-013B-noc-core/01-NODE-HEALTH-FAILURE-RECOVERY-EVIDENCE.md`

Cubre validación física y operacional de Node Health, falla crítica,
impacto observable sobre streaming, separación respecto de Stream Health
y recuperación automática del nodo.

### Block 2 / Stream Health Contract and Temporal Health

Documentos:

- `ENG-013B-noc-core/02-STREAM-HEALTH-CONTRACT.md`
- `ENG-013B-noc-core/03-STREAM-HEALTH-TEMPORAL-EVIDENCE.md`

Cubre el contrato multiprotocolo de Stream Health, semántica canónica de
Health, histéresis temporal, prevención de flapping y validación física SRT.

### Blocks 3–4 / Health Transitions and Events Integration

La evolución correspondiente se documenta dentro del README y de la
evidencia acumulada del núcleo NOC.

Cubre detección semántica de transiciones y persistencia mediante la
infraestructura existente de Events.

### Block 5 / Alarm Policy Integration

Documento:
`ENG-013B-noc-core/04-STREAM-HEALTH-ALARM-POLICY-EVIDENCE.md`

Cubre separación entre Health, Events y Alarms; decisiones NONE, RAISE,
KEEP y RESOLVE; prevención de alarm storms; persistencia durable y
validación física stable/no-flood.

### Block 6 / Aggregation

Documento:
`ENG-013B-noc-core/05-STREAM-HEALTH-AGGREGATION-EVIDENCE.md`

Cubre la jerarquía observada conexión → protocolo → servicio → plataforma,
la autoridad poblacional de SessionSnapshot, precedencia de Health SRT,
fallback a SessionQuality, semántica UNKNOWN y validación física
observed-only.

Resultado de regresión completa de Block 6:

```text
3228 passed
0 failed
1 warning
```

### Block 7 / Dashboard

Documento:
`ENG-013B-noc-core/06-PLATFORM-HEALTH-DASHBOARD-EVIDENCE.md`

Cubre la proyección de PlatformHealth hacia presentación, transporte por
DashboardApplication y DashboardSnapshotService, PlatformHealthRenderer,
integración incremental del panel PLATFORM HEALTH, separación respecto de
STREAM HEALTH y NODE HEALTH, procedencia temporal independiente y
validación física en ejtv-01.

La prueba física confirmó:

```text
MediaMTX paths:          3
Observed services:      2
PLATFORM HEALTH:        HEALTHY
Worst:                  HEALTHY
Coverage:               100%
Affected:               0%
H:2 D:0 C:0 U:0
```

La integración físicamente confirmó el principio observed-only:

```text
ABSENCE != FAILURE
```

Resultado de regresión completa de Block 7:

```text
3249 passed
0 failed
1 warning
65.16 seconds
```

El warning restante corresponde a la deprecación conocida de
Starlette/httpx TestClient y no está relacionado con Block 7.

## Estado de cierre

Blocks 1–6 cuentan con evidencia técnica y validación completadas.

Block 7 cuenta con implementación, prueba física y regresión completa
en verde.

El cierre formal de Block 7 queda pendiente únicamente de revisión final
del diff, commit, push y verificación de sincronización con origin.
