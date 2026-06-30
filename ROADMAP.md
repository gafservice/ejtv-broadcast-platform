# ROADMAP

## EJTV Broadcast Platform

**Estado del proyecto:** Fase II en desarrollo

**Última actualización:** 2026-06-30

---

# 1. Propósito

Este documento define la hoja de ruta de desarrollo de la **EJTV Broadcast Platform**.

Su objetivo es mantener una visión clara del avance técnico del proyecto, las misiones completadas, las etapas pendientes y la dirección de evolución de la plataforma.

El ROADMAP no sustituye las Misiones, los Baselines, los CHANGELOG ni la documentación técnica; su función es proporcionar una visión ejecutiva del estado general del proyecto.

---

# 2. Estado actual

Al cierre de la **MISSION-013**, la plataforma dispone de una infraestructura multimedia funcional compuesta por:

* Ubuntu Server 24.04.4 LTS.
* Servicio SSH.
* Cockpit.
* Firewall UFW.
* Sincronización horaria mediante `systemd-timesyncd`.
* MediaMTX v1.19.0.
* FFmpeg 6.1.1.
* RTMP completamente implementado y validado.
* SRT completamente implementado y validado.
* Documentación técnica estructurada.
* CHANGELOG por misión.
* Baselines por misión.
* Acceptance Tests.
* Scripts de mantenimiento.
* Arquitectura documental consolidada.

---

# 3. Fases del proyecto

## Fase I — Infraestructura base

**Estado:** ✅ Completada

**Objetivo**

Construir la base operativa del servidor Ubuntu, incluyendo administración remota, seguridad inicial, sincronización horaria y estructura documental.

| Misión      | Estado | Descripción                            |
| ----------- | :----: | -------------------------------------- |
| MISSION-001 |    ✅   | Preparación inicial del proyecto       |
| MISSION-002 |    ✅   | Organización documental                |
| MISSION-003 |    ✅   | Consolidación del entorno base         |
| MISSION-004 |    ✅   | Consolidación del entorno base         |
| MISSION-005 |    ✅   | Consolidación de infraestructura       |
| MISSION-006 |    ✅   | Preparación de servicios base          |
| MISSION-007 |    ✅   | Consolidación de infraestructura       |
| MISSION-008 |    ✅   | Preparación del entorno operativo      |
| MISSION-009 |    ✅   | Servicio oficial de sincronización NTP |

---

## Fase II — Infraestructura multimedia

**Estado:** 🚧 En desarrollo

**Objetivo**

Implementar los protocolos de contribución y distribución multimedia soportados por MediaMTX.

| Misión      | Estado | Descripción                  |
| ----------- | :----: | ---------------------------- |
| MISSION-010 |    ✅   | MediaMTX                     |
| MISSION-011 |    ✅   | FFmpeg                       |
| MISSION-012 |    ✅   | RTMP                         |
| MISSION-013 |    ✅   | SRT                          |
| MISSION-014 |    ⏳   | HLS                          |
| MISSION-015 |    ⏳   | WebRTC                       |
| MISSION-016 |    ⏳   | Validación extremo a extremo |

---

## Fase III — Seguridad y operación

**Estado:** Pendiente

**Objetivo**

Fortalecer la operación de la plataforma mediante servicios de seguridad, respaldo, monitoreo y automatización.

| Misión      | Estado | Descripción            |
| ----------- | :----: | ---------------------- |
| MISSION-017 |    ⏳   | Fail2ban               |
| MISSION-018 |    ⏳   | Certificados TLS       |
| MISSION-019 |    ⏳   | Sistema de Backups     |
| MISSION-020 |    ⏳   | Automatización inicial |
| MISSION-021 |    ⏳   | Monitoreo              |
| MISSION-022 |    ⏳   | Validación integral    |

---

## Fase IV — Producción

**Estado:** Pendiente

**Objetivo**

Preparar la plataforma para operación continua y despliegue estable.

| Misión      | Estado | Descripción                 |
| ----------- | :----: | --------------------------- |
| MISSION-023 |    ⏳   | Pruebas de carga            |
| MISSION-024 |    ⏳   | Optimización                |
| MISSION-025 |    ⏳   | Procedimientos operativos   |
| MISSION-026 |    ⏳   | Recuperación ante desastres |
| MISSION-027 |    ⏳   | Release 1.0                 |

---

# 4. Componentes implementados

| Componente    | Estado | Documento                   |
| ------------- | :----: | --------------------------- |
| Ubuntu Server |    ✅   | `docs/installation/`        |
| SSH           |    ✅   | `docs/services/ssh.md`      |
| Cockpit       |    ✅   | `docs/services/cockpit.md`  |
| Firewall UFW  |    ✅   | `docs/network/firewall.md`  |
| NTP           |    ✅   | `docs/services/ntp.md`      |
| MediaMTX      |    ✅   | `docs/services/mediamtx.md` |
| FFmpeg        |    ✅   | `docs/services/ffmpeg.md`   |
| RTMP          |    ✅   | `docs/services/rtmp.md`     |
| SRT           |    ✅   | `docs/services/srt.md`      |

# 5. Estado de los protocolos multimedia

| Protocolo | Estado |                Disponible desde                |
| --------- | :----: | :--------------------------------------------: |
| RTSP      |    ✅   |             MISSION-010 (MediaMTX)             |
| RTMP      |    ✅   |                   MISSION-012                  |
| SRT       |    ✅   |                   MISSION-013                  |
| HLS       |    ⏳   |                   MISSION-014                  |
| WebRTC    |    ⏳   |                   MISSION-015                  |
| MoQ       |    ⏳   | Soportado por MediaMTX (Implementación futura) |

---

# 6. Componentes pendientes

| Componente                      | Estado |
| ------------------------------- | :----: |
| OBS Studio                      |    ⏳   |
| NGINX                           |    ⏳   |
| PostgreSQL                      |    ⏳   |
| Grafana                         |    ⏳   |
| Prometheus                      |    ⏳   |
| Fail2ban                        |    ⏳   |
| Certificados TLS                |    ⏳   |
| Sistema de Backups              |    ⏳   |
| Sistema de monitoreo            |    ⏳   |
| Automatización de despliegue    |    ⏳   |
| Automatización de mantenimiento |    ⏳   |
| Integración continua (CI/CD)    |    ⏳   |


# 7. Criterio de avance

Una misión únicamente se considera finalizada cuando cumple satisfactoriamente con:

* Implementación funcional.
* Validación técnica.
* Documentación técnica.
* Baseline correspondiente.
* CHANGELOG actualizado.
* Acceptance Test.
* Scripts de mantenimiento, cuando apliquen.
* Revisión técnica final.

---

# 8. Próxima misión

## MISSION-014 — HLS

**Objetivo preliminar**

Implementar, configurar, validar y documentar completamente el protocolo **HTTP Live Streaming (HLS)** sobre MediaMTX, incorporando:

* implementación funcional;
* validación técnica;
* documentación del servicio;
* Acceptance Test;
* script de mantenimiento;
* actualización del CHANGELOG;
* actualización del ROADMAP;
* Baseline correspondiente;
* revisión técnica final.

---

# 9. Notas de ingeniería

Este ROADMAP es un documento vivo.

Debe actualizarse al cierre de cada misión para reflejar:

* nuevas implementaciones;
* cambios de arquitectura;
* incorporación de servicios;
* cierre de fases;
* nuevas líneas base;
* evolución técnica de la plataforma.

---

# 10. Hitos alcanzados

Al cierre de la **MISSION-013** se han alcanzado los siguientes hitos principales:

| Hito                                | Estado |
| ----------------------------------- | :----: |
| Plataforma Ubuntu instalada         |    ✅   |
| Arquitectura documental consolidada |    ✅   |
| Metodología basada en Misiones      |    ✅   |
| Sistema de Baselines                |    ✅   |
| CHANGELOG por misión                |    ✅   |
| Acceptance Tests                    |    ✅   |
| SSH operativo                       |    ✅   |
| Cockpit operativo                   |    ✅   |
| Firewall documentado                |    ✅   |
| NTP operativo                       |    ✅   |
| MediaMTX operativo                  |    ✅   |
| FFmpeg integrado                    |    ✅   |
| RTMP operativo                      |    ✅   |
| SRT operativo                       |    ✅   |
| Scripts de mantenimiento            |    ✅   |

Estos hitos constituyen la línea base funcional sobre la cual continuará evolucionando la plataforma.

---

# 11. Visión de largo plazo

La **EJTV Broadcast Platform** evolucionará de forma incremental hasta convertirse en una infraestructura completa para la recepción, procesamiento, administración y distribución profesional de contenido audiovisual sobre redes IP.

Entre los componentes previstos para futuras etapas se encuentran:

* OBS Studio.
* HLS.
* WebRTC.
* NGINX.
* PostgreSQL.
* Grafana.
* Prometheus.
* Sistema de monitoreo.
* Automatización de instalación.
* Automatización de mantenimiento.
* Sistema de respaldo y recuperación.
* Integración continua (CI/CD).

Toda nueva funcionalidad deberá incorporarse siguiendo la metodología oficial del proyecto basada en Misiones, Baselines, CHANGELOG, Acceptance Tests y documentación técnica.

---

# 12. Política de actualización

El presente documento deberá revisarse y actualizarse al finalizar cada misión.

Como mínimo deberán reflejarse:

* estado de las misiones;
* componentes implementados;
* componentes pendientes;
* protocolos soportados;
* hitos alcanzados;
* cambios en la dirección técnica del proyecto.

Ninguna misión podrá considerarse oficialmente cerrada sin verificar que este documento refleja correctamente el estado de la plataforma.

---

# Estado del ROADMAP

**Versión:** 1.3

**Estado:** Vigente

**Última misión incorporada:** MISSION-013

**Próxima revisión:** Al cierre de la MISSION-014.
