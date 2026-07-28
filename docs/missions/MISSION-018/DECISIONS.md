# DECISIONS — MISSION-018

**Misión:** MISSION-018

**Nombre:** Network Operations Center (NOC) Web

**Estado:** En desarrollo

---

# Introducción

Este documento recopila las principales decisiones arquitectónicas que sustentan el desarrollo de la MISSION-018.

Las decisiones se documentan formalmente mediante **Architecture Decision Records (ADR)** almacenados en:

```
docs/decisions/
```

Este documento funciona como índice de referencia para identificar rápidamente cuáles ADR impactan esta misión.

---

# Objetivos

- Mantener la trazabilidad de las decisiones arquitectónicas.
- Evitar duplicar información entre la misión y los ADR.
- Facilitar el mantenimiento del sistema.
- Documentar la evolución técnica del proyecto.

---

# ADR Relacionados

| ADR | Estado | Descripción |
|------|---------|-------------|
| ADR-001 | ✅ | Arquitectura base del proyecto |
| ADR-002 | ✅ | Organización documental |
| ADR-003 | ✅ | Arquitectura del Dashboard Terminal |
| ADR-004 | ✅ | Organización del módulo Engineering |
| ADR-005 | ✅ | Arquitectura del Dashboard Web |
| ADR-006 | ✅ | Arquitectura del módulo Identity |

---

# Decisiones Relevantes

## Arquitectura por capas

Se adopta una arquitectura desacoplada basada en:

- Dominio
- Servicios
- Adaptadores
- Presentación

Esta organización permite mantener independencia entre la lógica de negocio y la infraestructura.

---

## Dashboard modular

El Dashboard se divide en paneles independientes.

Cada panel posee:

- Modelo
- Renderer
- Servicios asociados

Esta decisión permite incorporar nuevas métricas sin afectar los componentes existentes.

---

## Integración con MediaMTX

La obtención de información operacional del sistema de streaming se realiza mediante adaptadores especializados.

Esto desacopla el Dashboard de la implementación específica del servidor de streaming.

---

## Métricas en tiempo real

Las métricas del sistema operativo y del servidor se obtienen en tiempo real evitando datos simulados.

Esta decisión convierte al Dashboard en una herramienta operacional del NOC.

---

## API REST

La arquitectura incorpora una API REST para desacoplar el backend del frontend web.

Esta decisión facilita:

- futuras interfaces gráficas;
- aplicaciones móviles;
- automatización;
- integraciones externas.

---

## Arquitectura evolutiva

La misión se desarrolla mediante incrementos funcionales documentados por Sprint.

Cada Sprint incorpora nuevas capacidades sin modificar la arquitectura general del sistema.

---

# Trazabilidad

| Área | Documento |
|-------|-----------|
| Arquitectura general | ARCHITECTURE.md |
| Evolución histórica | TIMELINE.md |
| Cambios funcionales | CHANGELOG.md |
| Ingeniería | docs/engineering/ |
| ADR | docs/decisions/ |

---

# Próximas decisiones previstas

Conforme evolucione la misión se documentarán nuevos ADR relacionados con:

- Alarm Management.
- Event Management.
- Reporting.
- Realtime Dashboard.
- Inteligencia Artificial aplicada al NOC.
- Automatización operativa.

---

# Referencias

- README.md
- TIMELINE.md
- CHANGELOG.md
- ARCHITECTURE.md
- docs/decisions/

# MISSION-018 — Decisiones Técnicas

## Propósito

Este documento registra las decisiones técnicas y metodológicas tomadas durante el desarrollo de la **MISSION-018**.

Su objetivo es explicar **por qué** se tomaron determinadas decisiones y servir como referencia para futuras modificaciones de la plataforma.

---

# Principios

## 1. Código primero

La implementación tiene prioridad sobre la documentación.

La documentación debe describir el software existente y nunca convertirse en una especificación desconectada de la realidad.

---

## 2. Una sola fuente de verdad

Toda decisión permanente de arquitectura deberá documentarse mediante un **ADR (Architecture Decision Record)** dentro de:

```text
docs/decisions/
```

Este documento únicamente resume las decisiones que afectan directamente a la misión.

---

## 3. Documentación mínima

Cada Sprint utilizará inicialmente un único archivo:

```text
README.md
```

Solamente cuando una sección crezca lo suficiente se dividirá en documentos independientes.

---

## 4. Desarrollo incremental

La misión avanza mediante pequeños incrementos verificables.

Cada Sprint debe producir software funcional y comprobable.

---

## 5. Evidencia

Toda funcionalidad deberá poder demostrarse mediante alguno de los siguientes elementos:

- pruebas automáticas;
- capturas de pantalla;
- registros del sistema;
- evidencia en consola;
- videos;
- métricas.

---

## 6. Calidad

No se considera terminado un Sprint mientras no existan evidencias suficientes que demuestren su funcionamiento.

---

# Decisiones vigentes

Hasta el momento se mantienen las siguientes decisiones:

- MediaMTX continúa siendo el núcleo del transporte multimedia.
- FFmpeg continúa siendo el motor principal de procesamiento.
- El backend será responsable de toda la lógica de negocio.
- El frontend consumirá únicamente servicios del backend.
- El Dashboard representa únicamente información real del sistema.
- Se prioriza software libre y componentes abiertos.
- La documentación deberá mantenerse ligera y fácil de mantener.

---

# Historial

Las nuevas decisiones importantes deberán registrarse mediante un ADR y resumirse posteriormente en este documento.