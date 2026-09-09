# ENG-013 — Changelog

Este documento resume la evolución técnica de ENG-013, con énfasis en
ENG-013B — NOC Core.

## ENG-013B — NOC Core

### Block 1 — Node Health Failure / Recovery

- consolidación del dominio Node Health;
- validación de falla crítica;
- separación entre Node Health y Stream Health;
- recuperación automática del estado operacional;
- evidencia física documentada.

Estado: cerrado.

### Block 2 — Temporal Stream Health

- estabilización temporal de Stream Health;
- ventanas independientes de degradación y recuperación;
- histéresis contra flapping;
- conservación de telemetría actual;
- validación física SRT.

Estado: cerrado.

### Block 3 — Health Transitions

- detección semántica de transiciones sobre Health estabilizado;
- separación entre observación y cambio de estado;
- base para integración posterior con Events y Alarms.

Estado: cerrado.

### Block 4 — Events Integration

- integración de transiciones Stream Health con EventService;
- reutilización de persistencia durable existente;
- persistencia en SQLite y evidencia JSONL;
- sin introducción de subsistemas paralelos.

Estado: cerrado.

### Block 5 — Alarm Policy Integration

- políticas NONE, RAISE, KEEP y RESOLVE;
- reutilización de AlarmService;
- prevención de alarm storms;
- validación física stable/no-flood;
- persistencia durable de transiciones de alarma.

Estado: cerrado y verificado en origin.

### Block 6 — Aggregation

- incorporación de HealthPopulation;
- incorporación de ProtocolHealth;
- incorporación de ServiceHealth;
- incorporación de PlatformHealth;
- jerarquía conexión → protocolo → servicio → plataforma;
- autoridad observacional de SessionSnapshot;
- precedencia de Health SRT especializado;
- fallback a SessionQuality;
- semántica explícita de UNKNOWN;
- preservación del principio observed-only;
- integración mediante latest_platform_health.

Validación:

```text
69 aggregation tests passed
3228 backend tests passed
0 failed
1 warning
```

Estado: cerrado y sincronizado con origin.

### Block 7 — Dashboard

- incorporación de PlatformHealthPanelData;
- proyección pura PlatformHealth → presentación;
- transporte mediante DashboardApplication;
- transporte mediante DashboardSnapshotInput;
- transporte mediante DashboardSnapshotService;
- incorporación de PlatformHealthRenderer;
- integración incremental del panel PLATFORM HEALTH;
- conservación de STREAM HEALTH;
- conservación de NODE HEALTH;
- preservación del layout histórico del dashboard;
- separación estricta entre dominio Health y presentación.

Durante la primera validación física se detectó una suposición temporal
incorrecta: PlatformHealth.captured_at se comparaba contra el timestamp de
MediaMTXSnapshot aunque PlatformHealth deriva de SessionSnapshot.

La prueba física registró:

```text
MediaMTXSnapshot : 2026-09-09 21:30:41.709130+00:00
SessionSnapshot  : 2026-09-09 21:30:41.714707+00:00
Delta            : 5.577 ms
```

La corrección eliminó únicamente esa igualdad inválida y preservó la
procedencia temporal independiente de PlatformHealth.

No se introdujo tolerancia arbitraria de tiempo.

La segunda validación física confirmó:

```text
STREAM HEALTH    HEALTHY
PLATFORM HEALTH  HEALTHY
NODE HEALTH      HEALTHY

MediaMTX paths   3
Observed services 2
Coverage         100%
Affected         0%
H:2 D:0 C:0 U:0
```

La presencia del path enlace sin sesión observada no creó población fantasma
en Platform Health, confirmando nuevamente:

```text
ABSENCE != FAILURE
```

Validación final:

```text
3249 backend tests passed
0 failed
1 warning
65.16 seconds
```

`python -m compileall -q app tests` completó sin errores.

`git diff --check` completó sin errores.

La primera regresión completa se detuvo durante collection porque el entorno
virtual no contenía reportlab, aunque la dependencia ya estaba declarada en
requirements.txt. El entorno fue reparado sin modificar código ni archivos
de dependencias.

Estado: implementación, pruebas y evidencia completadas. Cierre Git pendiente
de revisión final, staging selectivo, commit, push y verificación origin.
