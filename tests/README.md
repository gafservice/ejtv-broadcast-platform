# EJTV Broadcast Test Lab

## Estado

🚧 Fase 1 — Estructura inicial

---

# 1. Objetivo

El EJTV Broadcast Test Lab es el banco de pruebas oficial de la plataforma EJTV Broadcast Platform.

Su propósito es permitir la generación, publicación, recepción, validación y documentación de señales multimedia utilizadas durante las pruebas técnicas de la plataforma.

---

# 2. Alcance

El laboratorio permitirá validar:

- señales sintéticas;
- archivos multimedia;
- perfiles broadcast;
- publicación mediante RTSP, RTMP y SRT;
- recepción mediante RTSP, RTMP, SRT, HLS y WebRTC;
- consumo de recursos;
- estabilidad;
- interoperabilidad;
- pruebas de regresión.

---

# 3. Organización

```text
tests/
├── media/
├── profiles/
├── publishers/
├── receivers/
├── benchmarks/
├── reports/
└── acceptance/

EJTV Broadcast Test Lab

Version: 1.0

Estado:

Operational