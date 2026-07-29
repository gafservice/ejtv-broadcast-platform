# CHANGELOG — MISSION-018

**Misión:** MISSION-018

**Nombre:** Network Operations Center (NOC) Web

**Estado:** En desarrollo

---

# Introducción

Este documento resume los principales cambios incorporados durante el desarrollo de la MISSION-018.

A diferencia de la línea de tiempo (TIMELINE.md), este documento presenta una visión ejecutiva de las capacidades agregadas a la plataforma conforme evolucionó el proyecto.

Cada entrada representa un incremento funcional importante que modifica la arquitectura, las capacidades operativas o la experiencia de monitoreo del NOC Web.

---

# Resumen General

| Sprint | Estado | Resultado |
|---------|---------|-----------|
| Sprint 001 | ✅ | Arquitectura inicial del Control Center |
| Sprint 002 | ✅ | Abstracción de infraestructura |
| Sprint 003 | ✅ | Consolidación del Control Center |
| Sprint 004 | ✅ | Service Monitoring |
| Sprint 005 | ✅ | Observabilidad del sistema y Dashboard Terminal |
| Sprint 006 | ✅ | Active Clients y métricas avanzadas de Streaming |
| Sprint 007 | ✅ | Fundación de la REST API del Dashboard |

---

# Cambios por Sprint

## Sprint 001 — Control Center Architecture

### Agregado

- Arquitectura inicial del Control Center.
- Organización base del módulo NOC.
- Definición de la estructura general del proyecto.

### Resultado

Se establecen las bases arquitectónicas sobre las cuales evolucionará el NOC Web.

---

## Sprint 002 — Infrastructure Abstraction

### Agregado

- Abstracción de componentes dependientes de la infraestructura.
- Separación entre dominio, servicios y adaptadores.
- Mejora de la extensibilidad del sistema.

### Resultado

La plataforma reduce el acoplamiento con la infraestructura física y facilita futuras integraciones.

---

## Sprint 003 — Consolidación del Control Center

### Agregado

- Reorganización documental.
- Normalización de módulos.
- Consolidación del Control Center como núcleo operativo.

### Resultado

Se estabiliza la organización del proyecto antes de incorporar nuevas capacidades funcionales.

---

## Sprint 004 — Service Monitoring

### Agregado

- Monitoreo de servicios del servidor.
- Visualización del estado operativo.
- Integración inicial de métricas de infraestructura.

### Resultado

El NOC obtiene visibilidad del estado de los servicios críticos.

---

## Sprint 005 — System Observability

### Agregado

- Dashboard Terminal basado en Rich.
- Métricas reales de CPU.
- Memoria.
- Disco.
- Interfaces de red.
- Throughput de red.
- Integración de métricas del sistema operativo.
- Health Dashboard para Streaming.

### Resultado

El Dashboard Terminal deja de utilizar datos simulados y comienza a representar el estado real del servidor.

---

## Sprint 006 — Active Clients

### Agregado

- Arquitectura de clientes activos.
- Integración con sesiones de MediaMTX.
- Panel de sesiones.
- Métricas de streaming.
- Modelos de calidad de sesiones.
- Dashboard enriquecido para monitoreo operacional.

### Resultado

El NOC incorpora información operacional de clientes conectados y sesiones activas de streaming.

---

## Sprint 007 — REST API Foundation

### Agregado

- Fundación de la API REST.
- Endpoint inicial del Dashboard.
- Preparación para integración con el frontend web.

### Resultado

Se establece la capa de comunicación entre el backend y la futura interfaz web.

---

# Cambios Arquitectónicos Relevantes

Durante la evolución de la misión se incorporaron mejoras significativas en la arquitectura:

- Dashboard modular.
- Servicios desacoplados.
- Arquitectura basada en dominio.
- Adaptadores para MediaMTX.
- Modelos especializados para paneles.
- Renderizadores independientes.
- Métricas del sistema en tiempo real.
- Arquitectura de sesiones activas.
- Integración con API REST.

---

# Estado Actual

Al cierre de esta actualización, la MISSION-018 dispone de:

- Dashboard Terminal operativo.
- Métricas reales del servidor.
- Monitoreo de servicios.
- Métricas de Streaming.
- Clientes activos.
- Integración con MediaMTX.
- Base para REST API.
- Arquitectura preparada para frontend web.

---

# Próximos Incrementos

Las siguientes capacidades continuarán ampliando la misión:

- Identity.
- Dashboard Web.
- Alarm Management.
- Event Management.
- Reporting.
- Analytics.
- Automatización.
- IA aplicada a operaciones.

---

# Referencias

- README.md
- TIMELINE.md
- ARCHITECTURE.md
- DECISIONS.md
- docs/engineering/