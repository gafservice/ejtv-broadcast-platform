# MISSION-018 — NOC Web

**Estado:** En desarrollo

**Versión:** 1.0

**Inicio:** 2026-07

**Área:** Plataforma Web / NOC

---

# 1. Introducción

La **MISSION-018** tiene como objetivo desarrollar el **Network Operations Center (NOC) Web** de la plataforma.

Esta misión representa la transición desde herramientas de administración orientadas a consola hacia una plataforma web moderna que permita visualizar, supervisar y administrar el estado operativo del sistema desde un navegador.

El NOC Web reutiliza los servicios existentes del backend, garantizando que tanto el Dashboard Terminal como la interfaz web consuman la misma información operacional, evitando la duplicación de lógica de negocio.

---

# 2. Objetivo General

Diseñar e implementar una interfaz web para la supervisión y administración de la plataforma, proporcionando una experiencia moderna, segura y escalable para operadores, administradores y personal técnico.

---

# 3. Objetivos Específicos

Durante esta misión se desarrollarán las capacidades necesarias para:

- construir la interfaz web del NOC;
- integrar el backend existente con el frontend;
- implementar autenticación y control de acceso;
- visualizar métricas operacionales en tiempo real;
- administrar sesiones activas;
- incorporar alarmas y eventos;
- mantener la arquitectura limpia y modular de la plataforma.

---

# 4. Alcance

La misión comprende el desarrollo del NOC Web, incluyendo:

- interfaz de usuario;
- autenticación;
- dashboard principal;
- integración con la API;
- visualización de métricas;
- monitoreo de sesiones;
- alarmas;
- eventos;
- herramientas de diagnóstico;
- componentes reutilizables.

Quedan fuera del alcance aquellas funcionalidades que correspondan a la infraestructura base del sistema o a futuras misiones.

---

# 5. Arquitectura

La arquitectura funcional de esta misión se documenta en:

```
docs/architecture/
```

En particular:

- ARCHITECTURE.md
- IDENTITY.md
- MODULES.md
- DATA_MODEL.md

Las decisiones arquitectónicas adoptadas durante esta misión se registran mediante los correspondientes Architecture Decision Records (ADR).

---

# 6. Organización de la Misión

La misión se estructura mediante sprints incrementales.

```
MISSION-018
│
├── README.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── DECISIONS.md
├── CHANGELOG.md
│
└── sprints/
```

Cada sprint representa una entrega incremental de funcionalidades.

---

# 7. Sprints

Actualmente la misión contempla los siguientes sprints:

| Sprint | Objetivo |
|---------|----------|
| SPRINT-001 | Web Foundation |
| SPRINT-002 | Identity |
| SPRINT-003 | Realtime |
| SPRINT-004 | Alarms |
| SPRINT-005 | Events |
| SPRINT-006 | Streaming |
| SPRINT-007 | Diagnostics |

La planificación podrá ajustarse conforme evolucione el proyecto.

---

# 8. Relación con otras áreas

La MISSION-018 interactúa con múltiples componentes de la plataforma.

Entre ellos:

- Backend FastAPI
- Dashboard Services
- Dashboard Collector
- Dashboard Snapshot
- MediaMTX
- Linux
- React
- TypeScript
- API REST

Asimismo, esta misión contribuye a la evolución de diversas áreas de ingeniería documentadas en:

```
docs/engineering/
```

---

# 9. Documentación Asociada

La documentación de la misión se organiza en los siguientes documentos:

| Documento | Propósito |
|------------|-----------|
| README.md | Descripción general de la misión |
| ROADMAP.md | Planificación general |
| ARCHITECTURE.md | Arquitectura específica de la misión |
| DECISIONS.md | Índice de ADR relacionados |
| CHANGELOG.md | Evolución funcional de la misión |

Cada sprint dispone además de su propia documentación técnica y de implementación.

---

# 10. Estado Actual

La misión se encuentra en fase de desarrollo.

Las actividades actuales se concentran en:

- consolidación de la arquitectura documental;
- implementación del módulo de Identidad;
- integración del frontend con el backend;
- preparación del Dashboard Web.

---

# 11. Criterios de Finalización

La misión se considerará finalizada cuando:

- el NOC Web permita autenticación segura;
- el Dashboard Web consuma datos reales;
- las métricas operacionales se visualicen correctamente;
- el monitoreo de sesiones se encuentre integrado;
- el sistema de alarmas y eventos esté operativo;
- la documentación y las pruebas se encuentren completas.

---

# 12. Referencias

- `docs/architecture/`
- `docs/decisions/`
- `docs/engineering/`
- `docs/missions/MISSION-018/ROADMAP.md`
- `docs/missions/MISSION-018/CHANGELOG.md`