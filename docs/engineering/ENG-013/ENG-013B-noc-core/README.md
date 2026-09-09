# ENG-013B — NOC Core

Este directorio documenta la implementación, los contratos
arquitectónicos y la validación operacional del núcleo NOC asociado al
Node SDK.

## Documentos

### `01-NODE-HEALTH-FAILURE-RECOVERY-EVIDENCE.md`

Evidencia de validación física y operacional de Node Health:

- política de interfaces;
- detección de falla crítica;
- impacto observable sobre streaming;
- separación semántica entre Node Health y Stream Health;
- recuperación automática;
- recuperación integral del Node sin reiniciar el NOC.

### `02-STREAM-HEALTH-CONTRACT.md`

Contrato arquitectónico de evolución de Stream Health dentro de
ENG-013B.

Define, entre otros aspectos:

- arquitectura multiprotocolo y multiservicio;
- evaluación de salud por conexión, protocolo, servicio y plataforma;
- reutilización del `HealthStatus` canónico;
- tratamiento explícito de `UNKNOWN`;
- separación entre Health, Events, Alarms y History/Evidence;
- integración con los servicios de Events y Alarm lifecycle existentes;
- políticas de agregación y prevención de alarm storms;
- evolución incremental desde SRT Health hacia RTMP, RTSP, HLS y WebRTC;
- estrategia de pruebas, regresión, validación física y cierre de ENG-013B.

### `03-STREAM-HEALTH-TEMPORAL-EVIDENCE.md`

Evidencia de validación de Block 2 — Temporal Health:

- persistencia de degradación;
- histéresis de recuperación;
- prevención de flapping;
- conservación de telemetría actual;
- validación física SRT;
- regresión automatizada y completa del backend.

### Block 3 — Health Transitions

Implementa la detección semántica de transiciones de Stream Health sobre el estado temporal estabilizado, evitando que las capas posteriores vuelvan a detectar cambios de estado.

### Block 4 — Events Integration

Integra las transiciones semánticas de Stream Health con la infraestructura existente de Events del NOC. La transición detectada por Block 3 se transforma en un `EventRecord` y se persiste mediante el `EventService` existente, reutilizando SQLite y la proyección de evidencia JSONL sin introducir un subsistema paralelo.


### `04-STREAM-HEALTH-ALARM-POLICY-EVIDENCE.md`

Evidencia de implementación y validación de Block 5 — Alarm Policy Integration. Documenta la separación entre Health, Events y Alarms; las decisiones `NONE`, `RAISE`, `KEEP` y `RESOLVE`; la reutilización del `AlarmService` y del almacenamiento durable existentes; la prevención de alarm storms; la regresión automatizada; y la validación física stable/no-flood. La transición física controlada fue completada con degradación y recuperación reales, persistencia durable en SQLite y JSONL, y ausencia de alarmas espurias. Block 5 se encuentra cerrado y verificado en origin.

### `05-STREAM-HEALTH-AGGREGATION-EVIDENCE.md`

Evidencia de implementación y validación de Block 6 — Aggregation.
Documenta la jerarquía observada conexión → protocolo → servicio →
plataforma; `HealthPopulation`, `ProtocolHealth`, `ServiceHealth` y
`PlatformHealth`; la autoridad poblacional de `SessionSnapshot`; la
precedencia de Health especializado SRT y el fallback a `SessionQuality`;
la semántica explícita de `UNKNOWN`; la separación entre agregación,
Expected Presence, Events, Alarms y presentación; la integración mediante
`latest_platform_health`; la regresión completa del backend; y la
validación física contra sesiones SRT reales de `ejtv` e `impact`.
