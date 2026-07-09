# MISSION-016 — End-to-End Platform Validation

## Estado

✅ Finalizada

---

# 1. Objetivo

Validar el funcionamiento integral de la plataforma **EJTV Broadcast Platform** verificando que todos los protocolos multimedia implementados operen correctamente de forma individual y conjunta.

Esta misión constituye la validación integral de la arquitectura multimedia desarrollada durante las misiones M010–M015 y confirma el funcionamiento conjunto de todos los protocolos implementados sobre la plataforma EJTV Broadcast Platform.

---

# 2. Alcance

La validación comprende:

- MediaMTX
- FFmpeg
- RTSP
- RTMP
- SRT
- HLS
- WebRTC

No se incorporan nuevos servicios.

No se modifican configuraciones previamente validadas.

La misión consiste exclusivamente en verificar el correcto funcionamiento integrado de la plataforma.

---

# 3. Objetivos de validación

Durante esta misión deberán comprobarse los siguientes aspectos:

- funcionamiento individual de cada protocolo
- funcionamiento simultáneo
- interoperabilidad
- estabilidad
- consumo de recursos
- operación continua
- disponibilidad de todos los servicios

---

# 4. Arquitectura validada

```
                FFmpeg
                   │
                   ▼
              MediaMTX
     ┌────────┬────────┬────────┬────────┐
     ▼        ▼        ▼        ▼        ▼
   RTSP     RTMP      SRT      HLS    WebRTC
```

La plataforma utiliza un único origen multimedia administrado por FFmpeg y distribuido mediante MediaMTX hacia todos los protocolos soportados.

---

# 5. Componentes involucrados

Sistema operativo

- Ubuntu Server 24.04.4 LTS

Servicios

- SSH
- Cockpit
- UFW
- systemd-timesyncd
- MediaMTX v1.19.2
- FFmpeg 6.1.1

Protocolos

- RTSP
- RTMP
- SRT
- HLS
- WebRTC

---

# 6. Estrategia de validación

La validación se divide en cinco etapas.

## Etapa 1

Validación individual.

Cada protocolo debe operar correctamente de manera independiente.

---

## Etapa 2

Interoperabilidad.

Todos los protocolos deben compartir el mismo flujo multimedia sin interferencias.

---

## Etapa 3

Operación simultánea.

Todos los protocolos permanecerán activos de manera concurrente.

---

## Etapa 4

Estabilidad.

La plataforma permanecerá operando durante un período prolongado sin degradación del servicio.

---

## Etapa 5

Consumo de recursos.

Se registrarán los siguientes parámetros:

- CPU
- memoria
- utilización de red
- procesos
- servicios activos

---

| Validación | Estado |
|------------|:------:|
| RTSP | ✅ |
| RTMP | ✅ |
| SRT | ✅ |
| HLS | ✅ |
| WebRTC | ✅ |
| Operación simultánea | ✅ |
| Interoperabilidad | ✅ |
| Estabilidad | ✅ |
| Recursos | ✅ |
| Acceptance Test | ✅ |

---

# 8. Evidencias

Durante la misión deberán recopilarse evidencias de:

- capturas VLC
- capturas navegador
- logs MediaMTX
- logs FFmpeg
- consumo CPU
- consumo RAM
- puertos abiertos
- procesos activos
- estadísticas de red
- 
Adicionalmente se documentaron:

- validación mediante `ffprobe`;
- validación WebRTC desde navegador;
- verificación de versiones de MediaMTX y FFmpeg;
- verificación de puertos multimedia;
- monitoreo de consumo de CPU y memoria;
- análisis de registros de MediaMTX;
- validación complementaria de un flujo HEVC 1920×1080 con audio AAC sobre RTSP y SRT.

---

# 9. Criterios de aceptación

La misión será considerada satisfactoria cuando:

- todos los protocolos funcionen correctamente;
- todos los protocolos operen simultáneamente;
- no existan interrupciones del servicio;
- MediaMTX permanezca estable;
- FFmpeg permanezca estable;
- no existan reinicios inesperados;
- el consumo de recursos sea consistente;
- todos los Acceptance Test sean aprobados.
- **Resultado obtenido:** ✅ Cumplido.

---

# 10. Entregables

- Documento técnico
- Acceptance Test
- Script de mantenimiento (si aplica)
- CHANGELOG-M016
- Actualización CHANGELOG
- Actualización ROADMAP
- Baseline BL-016
- Documento de misión
- Revisión técnica final

---

# 11. Resultado obtenido

La MISSION-016 concluye satisfactoriamente con la validación extremo a extremo de la plataforma EJTV Broadcast Platform.

Se confirmó la operación integrada de MediaMTX y FFmpeg, así como la distribución de un único flujo multimedia mediante RTSP, RTMP, SRT, HLS y WebRTC.

La plataforma demostró estabilidad operativa, interoperabilidad entre protocolos y un consumo de recursos adecuado durante las pruebas realizadas, estableciendo la línea base de una arquitectura multimedia multiprotocolo completamente funcional.

# Lecciones aprendidas

Durante la validación se identificaron los siguientes aspectos relevantes:

- Los eventos `deadline exceeded while waiting connection` en WebRTC corresponden a negociaciones ICE no completadas y no representan fallos de la plataforma.
- La validación funcional de Low-Latency HLS debe realizarse con herramientas como `ffprobe`; las solicitudes `HTTP HEAD` mediante `curl` pueden devolver respuestas 404 sin afectar el funcionamiento del servicio.
- RTMP presenta limitaciones para el transporte de audio Opus; para escenarios de producción se recomienda utilizar AAC.
- La plataforma demostró compatibilidad preliminar con flujos HEVC 1920×1080, recomendándose una futura validación con señales broadcast reales 1080i59.94 provenientes del equipamiento de la estación.