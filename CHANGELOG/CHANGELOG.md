# CHANGELOG

Registro cronológico de los cambios relevantes realizados sobre la **EJTV Broadcast Platform**.

Cada misión concluida genera su propio documento de CHANGELOG, permitiendo mantener la trazabilidad de las decisiones técnicas, las implementaciones realizadas, las validaciones efectuadas y la documentación incorporada durante el desarrollo del proyecto.

---

# Índice de misiones

| Fecha      | Misión            | Descripción                         | Estado |
| ---------- | ----------------- | ----------------------------------- | :----: |
| 2026-06-26 | CHANGELOG-m001.md | Preparación inicial del servidor    |    ✅   |
| 2026-06-26 | CHANGELOG-m002.md | Actualización del sistema operativo |    ✅   |
| 2026-06-26 | CHANGELOG-m003.md | Configuración base del servidor     |    ✅   |
| 2026-06-26 | CHANGELOG-m004.md | Configuración de red                |    ✅   |
| 2026-06-26 | CHANGELOG-m005.md | Hardening inicial del sistema       |    ✅   |
| 2026-06-26 | CHANGELOG-m006.md | Servicio SSH                        |    ✅   |
| 2026-06-26 | CHANGELOG-m007.md | Cockpit                             |    ✅   |
| 2026-06-26 | CHANGELOG-m008.md | Firewall UFW                        |    ✅   |
| 2026-06-29 | CHANGELOG-m009.md | Sincronización NTP                  |    ✅   |
| 2026-06-29 | CHANGELOG-m010.md | MediaMTX                            |    ✅   |
| 2026-06-29 | CHANGELOG-m011.md | FFmpeg                              |    ✅   |
| 2026-06-30 | CHANGELOG-m012.md | RTMP                                |    ✅   |
| 2026-06-30 | CHANGELOG-m013.md | Secure Reliable Transport (SRT)     |    ✅   |

---

# Convenciones

Cada archivo de CHANGELOG correspondiente a una misión documenta, cuando aplica:

* Resumen de la misión.
* Implementación realizada.
* Infraestructura involucrada.
* Configuración aplicada.
* Cambios de seguridad.
* Reglas de firewall.
* Validaciones técnicas.
* Integración con la plataforma.
* Scripts incorporados.
* Documentación generada.
* Línea base (Baseline).
* Acceptance Test.
* Compatibilidad con componentes existentes.
* Incidentes detectados.
* Estado final de la misión.

Esta organización permite consultar de forma independiente la evolución técnica de cada etapa del proyecto, facilita la trazabilidad de los cambios realizados y proporciona un historial cronológico de la evolución de la plataforma **EJTV Broadcast Platform**.


# Versión 1.15

## MISSION-015 — WebRTC

### Fecha

30 de junio de 2026

### Nuevas funcionalidades

- Implementación oficial del servicio WebRTC sobre MediaMTX.
- Validación de distribución multimedia con latencia ultrabaja.
- Publicación RTSP mediante FFmpeg y conversión automática hacia WebRTC.
- Validación de negociación ICE.
- Validación de Peer Connection.
- Validación de transmisión de video H.264.
- Validación de transmisión de audio Opus.
- Actualización de MediaMTX desde la versión 1.19.0 hacia la versión 1.19.2.
- Incorporación del documento `docs/services/webrtc.md`.
- Incorporación del Acceptance Test `tests/mission-015-webrtc.md`.
- Incorporación del script `scripts/maintenance/webrtc-status.sh`.

### Estado

MISSION-015 completada satisfactoriamente.



## [MISSION-016] — Validación extremo a extremo

**Fecha:** 2026-07-01

### Agregado

- Validación integral de la plataforma multimedia EJTV Broadcast Platform.
- Verificación del funcionamiento conjunto de RTSP, RTMP, SRT, HLS y WebRTC.
- Validación de interoperabilidad entre todos los protocolos.
- Pruebas de operación simultánea utilizando un único flujo multimedia.
- Verificación de estabilidad operativa de MediaMTX y FFmpeg.
- Medición y registro del consumo de recursos del servidor.
- Acceptance Test de integración completado.
- Validación funcional mediante clientes RTSP, RTMP, SRT, HLS y WebRTC.
- Documentación técnica de la validación End-to-End.
- Baseline BL-016 incorporada.

### Observaciones

- RTMP distribuye únicamente el flujo de video cuando la fuente utiliza audio Opus; para producción se recomienda AAC.
- La validación HLS se realizó exitosamente mediante `ffprobe` en modo Low-Latency HLS.
- Se efectuó una validación complementaria con flujo HEVC 1920×1080 y audio AAC sobre RTSP y SRT, como referencia para futuras pruebas con señales broadcast reales.



## [MISSION-016] - Validación de OBS como fuente RTMP

### Agregado

- Validada la integración de OBS Studio como fuente de publicación RTMP hacia MediaMTX.
- Se verificó la publicación desde un equipo remoto (Ubuntu) y desde el propio servidor.
- Se definió el procedimiento estándar de configuración de OBS para la plataforma EJTV.
- Se validó la interoperabilidad con los protocolos RTMP, HLS, SRT y WebRTC.

### Validaciones realizadas

| Protocolo | Estado |
|-----------|:------:|
| RTMP | ✅ |
| HLS | ✅ |
| SRT | ✅ |
| WebRTC | ⚠ Video correcto, audio pendiente de revisión |
| RTSP | ⚠ Servicio operativo; pendiente apertura del puerto 8554/TCP en UFW |

### Incidencias encontradas

- OBS en Ubuntu presentaba cierre inesperado al agregar dispositivos V4L2 en ausencia de dispositivos `/dev/video*`.
- Se confirmó que la tarjeta DeckLink Mini Monitor corresponde únicamente a salida de video y no puede utilizarse como fuente de captura.
- Se detectó la ausencia de la regla UFW para el puerto 8554/TCP, impidiendo el acceso RTSP desde otros equipos de la red.















# MISSION-017 — Diseño Arquitectónico del EJTV Control Center

**Estado:** Finalizada

## Added

- Creación del subproyecto **EJTV Control Center**.
- Definición de la arquitectura general del sistema.
- Diseño del modelo de dominio.
- Definición de la API REST versión 1.
- Diseño del modelo inicial de roles y permisos.
- Definición de la navegación del sistema.
- Elaboración de la guía de estilo.
- Creación del README, ROADMAP y CHANGELOG propios del Control Center.
- Incorporación de la documentación técnica del Control Center.

## Changed

- La plataforma EJTV Broadcast Platform incorpora oficialmente una segunda línea de desarrollo orientada a la administración de la infraestructura multimedia.
- Se establece una separación formal entre la Plataforma Multimedia y el Control Center.

## Documentation

Se incorporaron los siguientes documentos:

```text
control-center/README.md
control-center/ROADMAP.md
control-center/CHANGELOG.md

control-center/docs/

ARCHITECTURE.md
MODULES.md
USER_STORIES.md
DATA_MODEL.md
API.md
PERMISSIONS.md
NAVIGATION.md
STYLE_GUIDE.md
```

## Next

MISSION-018

Fundación del Backend del EJTV Control Center.