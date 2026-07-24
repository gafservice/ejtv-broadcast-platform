# ENG-007 — Arquitectura

## Responsabilidad

Registro, normalización, persistencia y consulta de eventos operativos.

## Flujo de referencia

```text
Source
  ↓
Adapter
  ↓
Domain Model / Snapshot / Event
  ↓
Application Service
  ↓
API / Dashboard / Alarm / Diagnostic
```

## Dependencias

Documentar durante el refinamiento inicial del módulo.
