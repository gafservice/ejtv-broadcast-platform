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
