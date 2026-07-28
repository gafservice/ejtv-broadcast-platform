# TIMELINE — MISSION-018

**Misión:** MISSION-018

**Nombre:** Network Operations Center (NOC) Web

**Estado:** En desarrollo

---

# 1. Introducción

Este documento registra la evolución cronológica de la MISSION-018.

A diferencia de un roadmap tradicional, la línea de tiempo documenta los hitos reales del desarrollo, respaldados por el historial del repositorio Git y la documentación técnica asociada.

Cada entrada representa un incremento funcional significativo dentro del desarrollo del NOC Web.

---

# 2. Línea de Tiempo

| Fecha | Sprint | Hito | Estado |
|--------|---------|------|--------|
| 2026-07-09 | SPRINT-001 | Arquitectura inicial del Control Center | ✅ |
| 2026-07-12 | SPRINT-002 | Abstracción de infraestructura | ✅ |
| 2026-07 | SPRINT-003 | Consolidación de capacidades del Control Center | ✅ |
| 2026-07-19 | SPRINT-004 | Service Monitoring | ✅ |
| 2026-07-21 | SPRINT-005 | System Observability y Terminal Dashboard | ✅ |
| 2026-07-24 | SPRINT-006 | Active Clients y evolución del Dashboard | ✅ |
| 2026-07-27 | SPRINT-007 | REST API Foundation y Dashboard Endpoint | ✅ |

---

# 3. Evolución Funcional

## SPRINT-001 — Control Center Architecture

Se establece la arquitectura inicial del Control Center, definiendo las bases sobre las que evolucionará el NOC Web.

---

## SPRINT-002 — Infrastructure Abstraction

Se desacoplan los componentes dependientes de la infraestructura mediante capas de abstracción, facilitando la extensibilidad y las pruebas.

---

## SPRINT-003 — Consolidación del Control Center

Se reorganiza la documentación, se normaliza la estructura del proyecto y se incorporan nuevas capacidades al Control Center, preparando la plataforma para las siguientes etapas.

---

## SPRINT-004 — Service Monitoring

Se implementa el monitoreo de servicios como primer componente operativo del NOC.

---

## SPRINT-005 — System Observability

Se integran las métricas del sistema y el Dashboard Terminal, permitiendo visualizar el estado operativo del servidor desde una única interfaz.

---

## SPRINT-006 — Active Clients

Se incorpora la arquitectura de clientes activos, las métricas de MediaMTX y nuevas capacidades del Dashboard relacionadas con sesiones y streaming.

---

## SPRINT-007 — REST API Foundation

Se establece la base de la API REST del NOC Web y el endpoint inicial para el Dashboard, habilitando la integración con el frontend.

---

# 4. Próximas Etapas

Las siguientes funcionalidades continuarán ampliando la MISSION-018:

- Identity.
- Realtime Dashboard.
- Alarm Management.
- Event Management.
- Reporting.
- Administración Web.

Estas capacidades se desarrollarán en nuevos sprints conforme evolucione el proyecto.

---

# 5. Referencias

- README.md
- ARCHITECTURE.md
- DECISIONS.md
- CHANGELOG.md
- docs/engineering/