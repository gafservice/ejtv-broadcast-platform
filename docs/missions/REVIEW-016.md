# Revisión Técnica Final — MISSION-016

## MISSION-016 — Validación extremo a extremo

**Fecha:** 2026-07-01

**Estado:** ✅ Aprobada

---

# 1. Objetivo

Realizar la revisión técnica final de la MISSION-016 con el propósito de verificar que la plataforma EJTV Broadcast Platform cumple satisfactoriamente los objetivos definidos para la validación extremo a extremo de la infraestructura multimedia implementada durante las misiones M010–M015.

La presente revisión constituye el cierre técnico de la segunda fase del proyecto.

---

# 2. Alcance de la revisión

La revisión comprende:

- infraestructura del servidor;
- servicios base;
- MediaMTX;
- FFmpeg;
- protocolos multimedia;
- interoperabilidad;
- estabilidad operativa;
- consumo de recursos;
- documentación generada durante la misión.

---

# 3. Plataforma evaluada

## Sistema operativo

- Ubuntu Server 24.04.4 LTS

## Servicios

- SSH
- Cockpit
- Firewall UFW
- systemd-timesyncd

## Plataforma multimedia

- MediaMTX v1.19.2
- FFmpeg 6.1.1

---

# 4. Protocolos evaluados

Durante la revisión técnica se verificó la correcta operación de:

| Protocolo | Estado |
|-----------|:------:|
| RTSP | ✅ |
| RTMP | ✅ |
| SRT | ✅ |
| HLS | ✅ |
| WebRTC | ✅ |

Asimismo se comprobó la redistribución simultánea de un mismo flujo multimedia mediante todos los protocolos soportados por la plataforma.

---

# 5. Resultados de la validación

Las pruebas ejecutadas permitieron confirmar:

- funcionamiento individual de todos los protocolos;
- interoperabilidad completa mediante MediaMTX;
- publicación continua mediante FFmpeg;
- operación simultánea de múltiples clientes;
- estabilidad del servicio durante las pruebas;
- disponibilidad permanente de los servicios multimedia.

No se observaron interrupciones del servicio atribuibles a la arquitectura implementada.

---

# 6. Rendimiento observado

Durante la validación se registró:

## MediaMTX

- utilización aproximada de CPU: 5 %;
- memoria residente aproximada: 60 MB.

## FFmpeg

- utilización aproximada de CPU: 17 %;
- memoria residente aproximada: 60 MB.

## Sistema

- carga de CPU muy por debajo de la capacidad disponible;
- memoria suficiente para operación continua;
- ausencia de saturación del sistema.

Los recursos disponibles permiten considerar la plataforma apta para escenarios de operación con mayor carga, sujeto a las características del flujo multimedia y del número de clientes concurrentes.

---

# 7. Hallazgos técnicos

Durante la misión se documentaron los siguientes aspectos relevantes:

### RTMP

El protocolo distribuye correctamente video H.264.

Cuando la fuente utiliza audio Opus, la distribución de audio mediante RTMP puede verse limitada debido a las características propias del protocolo.

Para escenarios de producción se recomienda el uso de AAC.

---

### HLS

La validación funcional fue realizada mediante `ffprobe`.

Se comprobó que las solicitudes `HTTP HEAD` utilizando `curl` pueden devolver respuestas 404 en configuraciones Low-Latency HLS sin afectar el funcionamiento del servicio.

---

### WebRTC

Los eventos registrados como:

```
deadline exceeded while waiting connection
```

correspondieron a negociaciones ICE no completadas durante pruebas preliminares.

Una vez establecida correctamente la conexión WebRTC, no volvieron a registrarse dichos eventos.

No se identificaron fallos asociados a la arquitectura implementada.

---

### Compatibilidad HEVC

Se realizó una validación complementaria utilizando un flujo HEVC 1920×1080 con audio AAC.

El transporte fue validado correctamente mediante RTSP y SRT.

La validación definitiva con señales broadcast reales 1080i59.94 provenientes del equipamiento de producción queda propuesta como línea de evolución futura.

---

# 8. Riesgos residuales

Al cierre de la misión no se identifican riesgos críticos para la operación de la plataforma.

Como oportunidades de mejora se identifican:

- incorporación de mecanismos avanzados de monitoreo;
- endurecimiento de seguridad;
- automatización de respaldo;
- validación con señales broadcast reales;
- evaluación de escenarios de alta concurrencia.

Estas actividades corresponden a futuras fases del proyecto.

---

# 9. Conclusiones

La MISSION-016 demuestra que la arquitectura multimedia implementada cumple satisfactoriamente los objetivos definidos para la plataforma EJTV Broadcast Platform.

La combinación MediaMTX + FFmpeg permitió distribuir correctamente un único flujo multimedia mediante RTSP, RTMP, SRT, HLS y WebRTC, manteniendo estabilidad operativa y un consumo de recursos consistente.

La documentación generada durante la misión proporciona evidencia suficiente para respaldar la operación integrada de la plataforma y establece una línea base sólida para futuras etapas de evolución.

---

# 10. Cierre de la Fase II

Con la aprobación de la presente revisión técnica se declara oficialmente concluida la segunda fase del proyecto, correspondiente a la implementación y validación de la infraestructura multimedia.

A partir de este punto, las siguientes misiones estarán orientadas a fortalecer la plataforma mediante mecanismos de seguridad, monitoreo, automatización y preparación para escenarios de producción broadcast.

---

# 11. Dictamen técnico

**Resultado de la revisión:** ✅ APROBADA

La MISSION-016 cumple los criterios de aceptación establecidos y dispone de la documentación, evidencias y validaciones necesarias para ser considerada oficialmente finalizada.

En consecuencia, la plataforma **EJTV Broadcast Platform** queda establecida como una infraestructura multimedia multiprotocolo funcional, integrada y técnicamente validada.